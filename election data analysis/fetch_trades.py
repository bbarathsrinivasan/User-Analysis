import argparse
import logging
import os
import subprocess
import sys
import importlib.util
import time
from pathlib import Path
from typing import Any, Dict, List


DATA_ROOT = Path("./data")
def _import_db_writers():
	"""Return module-like object with write_metadata, write_prices, write_trades.

	Uses package import first, then file-path fallback.
	"""
	try:
		from polymarket_pipeline.db import writers as _writers  # type: ignore
		return _writers
	except Exception:
		import importlib.util, sys as _sys
		mod_path = Path(__file__).parent / "db" / "writers.py"
		spec = importlib.util.spec_from_file_location("writers", str(mod_path))
		if not spec or not spec.loader:
			raise
		_writers = importlib.util.module_from_spec(spec)  # type: ignore
		_sys.modules["writers"] = _writers  # type: ignore
		spec.loader.exec_module(_writers)  # type: ignore
		return _writers



def setup_logging() -> None:
	logging.basicConfig(
		level=logging.INFO,
		format="%(asctime)s | %(levelname)s | %(message)s",
		datefmt="%H:%M:%S",
	)


def ensure_dirs(event_slug: str) -> Dict[str, Path]:
	base = DATA_ROOT / event_slug / "meta"
	base.mkdir(parents=True, exist_ok=True)
	trades_base = DATA_ROOT / event_slug / "trades"
	trades_base.mkdir(parents=True, exist_ok=True)
	prices_base = DATA_ROOT / event_slug / "prices"
	prices_base.mkdir(parents=True, exist_ok=True)
	return {
		"meta_dir": base,
		# "meta_csv": base / "metadata.csv",
		"meta_named_csv": base / f"meta_{event_slug}.csv",
		"trades_dir": trades_base,
		"prices_dir": prices_base,
	}


def fetch_metadata_via_collector(event_slug: str) -> List[Dict[str, Any]]:
	"""Use collectors/metaDataCollector.py to fetch flattened metadata for an event.

	Tries to import the module and call its functions directly.
	If that fails, raises the exception to caller.
	"""
	# Try package import first
	try:
		from polymarket_pipeline.collectors import metaDataCollector as mdc  # type: ignore
	except Exception:
		# Fallback: import the collector by file path
		import importlib.util, sys as _sys
		mod_path = Path(__file__).parent / "collectors" / "metaDataCollector.py"
		spec = importlib.util.spec_from_file_location("metaDataCollector", str(mod_path))
		if not spec or not spec.loader:
			raise ImportError("Unable to import metaDataCollector from package or path")
		mdc = importlib.util.module_from_spec(spec)  # type: ignore
		_sys.modules["metaDataCollector"] = mdc  # type: ignore
		spec.loader.exec_module(mdc)  # type: ignore

	event = mdc.fetch_event(event_slug)  # type: ignore[attr-defined]
	rows = mdc.flatten_event_markets(event)  # type: ignore[attr-defined]
	# normalize to list[dict]
	return [dict(r) for r in rows]


def write_metadata_csv(rows: List[Dict[str, Any]], out_path: Path) -> None:
	if not rows:
		logging.info("No metadata rows for %s; skipping write.", out_path)
		return
	import csv

	fieldnames = sorted({k for r in rows for k in r.keys()})
	out_path.parent.mkdir(parents=True, exist_ok=True)
	with out_path.open("w", newline="", encoding="utf-8") as f:
		w = csv.DictWriter(f, fieldnames=fieldnames)
		w.writeheader()
		for r in rows:
			w.writerow(r)


def fetch_and_store_all_metadata(event_slugs: List[str]) -> None:
	setup_logging()
	logging.info("Fetching metadata for %d events via metaDataCollector.py", len(event_slugs))
	for slug in event_slugs:
		paths = ensure_dirs(slug)
		try:
			rows = fetch_metadata_via_collector(slug)
		except Exception as e:
			logging.error("%s: metadata fetch failed via collector: %s", slug, e)
			continue

		# Write named metadata CSV
		write_metadata_csv(rows, paths["meta_named_csv"])
		logging.info("%s: wrote %s", slug, paths["meta_named_csv"].name)
		# Also write to DB
		try:
			_writers = _import_db_writers()
			_writers.write_metadata(slug, rows)
		except Exception as e:
			logging.warning("%s: DB metadata write failed: %s", slug, e)


def _import_analyzer():
	"""Return analyze_event callable from analyze_events.py, with robust import fallback."""
	try:
		from polymarket_pipeline.analyze_events import analyze_event  # type: ignore
		return analyze_event
	except Exception:
		# Fallback: import by file path
		mod_path = Path(__file__).parent / "analyze_events.py"
		if not mod_path.exists():
			return None
		spec = importlib.util.spec_from_file_location("analyze_events", str(mod_path))
		if spec and spec.loader:
			mod = importlib.util.module_from_spec(spec)  # type: ignore
			sys.modules["analyze_events"] = mod  # type: ignore
			spec.loader.exec_module(mod)  # type: ignore
			return getattr(mod, "analyze_event", None)
	return None


def run_event_analysis(event_slug: str) -> None:
	"""Execute analysis for a single event.

	Prefers in-process import; falls back to subprocess with ONLY_EVENT_SLUG.
	"""
	analyze_event = _import_analyzer()
	if analyze_event is not None:
		try:
			logging.info("%s: running analysis (import)", event_slug)
			analyze_event(event_slug)
			logging.info("%s: analysis completed", event_slug)
			return
		except Exception as e:
			logging.warning("%s: analysis via import failed: %s; falling back to subprocess", event_slug, e)

	# Subprocess fallback: set ONLY_EVENT_SLUG and run analyze_events.py
	env = os.environ.copy()
	env["ONLY_EVENT_SLUG"] = event_slug
	cmd = [sys.executable, str(Path(__file__).parent / "analyze_events.py")]
	logging.info("%s: running analysis (subprocess)", event_slug)
	try:
		subprocess.run(cmd, env=env, check=True)
		logging.info("%s: analysis completed (subprocess)", event_slug)
	except subprocess.CalledProcessError as e:
		logging.error("%s: analysis subprocess failed: %s", event_slug, e)



def fetch_trades_direct_and_write(event_slug: str, out_dir: Path, concurrency: int = 1	) -> None:
	"""Fetch trades per market (using collectors' async coroutines), write CSV and Supabase DB in parallel.

	Writes one CSV per market as <market_slug>_trades.csv inside out_dir and inserts rows to Supabase DB.
	"""
	# Import collectors
	try:
		from polymarket_pipeline.collectors import dataCollectionScript as dcs  # type: ignore
	except Exception:
		import importlib.util, sys as _sys
		mod_path = Path(__file__).parent / "collectors" / "dataCollectionScript.py"
		spec = importlib.util.spec_from_file_location("dataCollectionScript", str(mod_path))
		if not spec or not spec.loader:
			raise ImportError("Unable to import dataCollectionScript from package or path")
		dcs = importlib.util.module_from_spec(spec)  # type: ignore
		_sys.modules["dataCollectionScript"] = dcs  # type: ignore
		spec.loader.exec_module(dcs)  # type: ignore

	import asyncio
	import aiohttp
	import csv

	async def run():
		timeout = aiohttp.ClientTimeout(total=None, connect=60, sock_read=300)  # No total timeout, 5min read timeout
		async with aiohttp.ClientSession(timeout=timeout) as session:
			event = await dcs.get_event_by_slug(session, event_slug)  # type: ignore[attr-defined]
			title = event.get("title") or event_slug
			markets = event.get("markets", [])
			logging.info("%s: event loaded: %s markets", event_slug, len(markets))
			sem = asyncio.Semaphore(concurrency)
			results = []
			completed = 0

			async def one_market(m):
				nonlocal completed
				slug = m.get("slug")
				cond = m.get("conditionId")
				if not slug or not cond:
					return None
				async with sem:
					# Stream fetch and write trades
					logging.info("%s: [%d/%d] fetching trades for market %s", event_slug, completed + 1, len(markets), slug)
					start_time = time.time()
					out_csv = out_dir / f"{slug}_trades.csv"
					w = None
					f = None
					total = 0
					batch_count = 0
					try:
						async for batch in dcs.iter_trades_batches(session, cond):  # type: ignore[attr-defined]
							if not batch:
								logging.warning("%s: received empty batch for market %s", event_slug, slug)
								continue
							batch_count += 1
							if w is None:
								f = out_csv.open("w", newline="", encoding="utf-8")
								w = csv.DictWriter(f, fieldnames=batch[0].keys())
								w.writeheader()
							w.writerows(batch)
							total += len(batch)
							if f:
								f.flush()
							# Log progress every 10 batches
							if batch_count % 10 == 0:
								logging.info("%s: market %s - processed %d batches, %d trades so far", event_slug, slug, batch_count, total)
					except Exception as e:
						logging.error("%s: error during batch iteration for market %s: %s", event_slug, slug, e)
						raise
					finally:
						if f:
							f.close()
					logging.info("%s: market %s - completed with %d batches totaling %d trades", event_slug, slug, batch_count, total)
					fetch_time = time.time() - start_time
					logging.info("%s: fetched %d trades for %s in %.2fs", event_slug, total, slug, fetch_time)
					# DB write - run in executor to avoid blocking event loop
					if total > 0:
						try:
							_writers = _import_db_writers()
							loop = asyncio.get_event_loop()
							logging.info("%s: writing %d trades to DB for market %s", event_slug, total, slug)
							db_start = time.time()
							# Re-read just-written CSV to stream into DB in batches to avoid holding memory
							def _read_rows():
								with out_csv.open("r", encoding="utf-8") as rf:
									reader = csv.DictReader(rf)
									return list(reader)
							rows = await loop.run_in_executor(None, _read_rows)
							await loop.run_in_executor(None, _writers.write_trades, event_slug, slug, rows)
							db_time = time.time() - db_start
							logging.info("%s: completed DB write for market %s in %.2fs", event_slug, slug, db_time)
						except Exception as e:
							logging.warning("%s: DB trades write failed for %s: %s", event_slug, slug, e)
					completed += 1
					return {"market_slug": slug, "trades_count": total}

			tasks = [asyncio.create_task(one_market(m)) for m in markets]
			return await asyncio.gather(*tasks, return_exceptions=True)

	asyncio.run(run())


def fetch_and_store_all_trades(event_slugs: List[str], concurrency: int = 1) -> None:
	setup_logging()
	logging.info("Fetching trades for %d events via dataCollectionScript.py", len(event_slugs))
	for slug in event_slugs:
		paths = ensure_dirs(slug)
		try:
			fetch_trades_direct_and_write(slug, paths["trades_dir"], concurrency)
			logging.info("%s: wrote per-market trade CSVs to %s", slug, paths["trades_dir"]) 
		except Exception as e:
			logging.error("%s: trades fetch failed via collector: %s", slug, e)


def fetch_prices_via_collector(event_slug: str, out_dir: Path) -> None:
	"""Use collectors/priceHistory.py to fetch price history for all markets in an event.

	Writes one CSV per market as <market_slug>_price.csv inside out_dir.
	"""
	# Try package import first
	try:
		from polymarket_pipeline.collectors import priceHistory as ph  # type: ignore
	except Exception:
		# Fallback: import the collector by file path
		import importlib.util, sys as _sys
		mod_path = Path(__file__).parent / "collectors" / "priceHistory.py"
		spec = importlib.util.spec_from_file_location("priceHistory", str(mod_path))
		if not spec or not spec.loader:
			raise ImportError("Unable to import priceHistory from package or path")
		ph = importlib.util.module_from_spec(spec)  # type: ignore
		_sys.modules["priceHistory"] = ph  # type: ignore
		spec.loader.exec_module(ph)  # type: ignore

	# Fetch event to get its markets, then loop markets and fetch price history per market
	event = ph.get_event_by_slug(event_slug)  # type: ignore[attr-defined]
	markets = event.get("markets", [])
	for m in markets:
		slug = m.get("slug")
		if not slug:
			continue
		out_csv = out_dir / f"{slug}_price.csv"
		try:
			rows = ph.fetch_market_price_history(slug, str(out_csv))  # type: ignore[attr-defined]
			# Also write to DB
			try:
				_writers = _import_db_writers()
				_writers.write_prices(event_slug, slug, rows)  # rows is a list[dict]
			except Exception as e:
				logging.warning("%s: DB prices write failed for %s: %s", event_slug, slug, e)
		except Exception as e:
			logging.warning("%s: price history failed for market %s: %s", event_slug, slug, e)


def fetch_and_store_all_prices(event_slugs: List[str]) -> None:
	setup_logging()
	logging.info("Fetching price history for %d events via priceHistory.py", len(event_slugs))
	for slug in event_slugs:
		paths = ensure_dirs(slug)
		try:
			fetch_prices_via_collector(slug, paths["prices_dir"])
			logging.info("%s: wrote per-market price CSVs to %s", slug, paths["prices_dir"]) 
			# Trigger per-event analysis once data is fetched
			run_event_analysis(slug)
		except Exception as e:
			logging.error("%s: price history fetch failed via collector: %s", slug, e)


# def parse_args() -> argparse.Namespace:
# 	p = argparse.ArgumentParser(description="Fetch Polymarket event metadata")
# 	p.add_argument("--event-slugs", nargs="+", required=True, help="List of event slugs")
# 	return p.parse_args()


if __name__ == "__main__":

# 	event_slugs = [
#   "maine-senate-election-winner",
#   "massachusetts-senate-election-winner",
#   "minnesota-senate-election-winner",
#   "mississippi-senate-election-winner",
#   "montana-senate-election-winner",
#   "nebraska-senate-election-winner",
#   "nebraska-senate-special-election",
#   "nevada-senate-democratic-primary-winner",
#   "nevada-senate-republican-primary-winner",
#   "new-jersey-senate-election-winner",
#   "ohio-senate-election-winner",
#   "tennessee-senate-election-winner",
#   "texas-senate-election-winner",
#   "virginia-senate-election-winner",
#   "virginia-senate-republican-primary-winner",
#   "west-virginia-senate-election-winner",
#   "who-will-replace-jd-vance-as-ohio-senator",
#   "who-will-replace-marco-rubio-as-florida-senator",
#   "will-fischer-win-nebraska-senate-election-by-7-points",
#   "florida-senate-election-winner",
#   "wyoming-senate-election-winner",
#   "new-mexico-senate-election-winner",
#   "delaware-senate-election-winner",
#   "rhode-island-senate-election-winner",
#   "who-will-win-dem-nomination-for-nyc-mayor",
#   "nyc-mayoral-dem-primary-mov",
#   "brad-lander-1st-round-of-vote-in-nyc-dem-mayoral-primary",
#   "zohran-mamdani-1st-round-of-vote-in-nyc-dem-mayoral-primary",
#   "andrew-cuomo-1st-round-of-vote-in-nyc-dem-mayoral-primary",
#   "nyc-mayoral-dem-primary-mamdani-mov",
#   "fl-1-special-election-jimmy-patronis-margin-of-victory",
#   "fl-6-special-election-randy-fine-margin-of-victory",
#   "mo-1-democratic-primary-winner",
#   "va-5-republican-primary-winner",
#   "fl-1-special-election-valimont-d-vs-patronis-r",
#   "fl-6-special-election-weil-d-vs-fine-r",
#   "new-jersey-governor-democratic-primary-winner",
#   "2nd-place-in-new-jersey-governor-democratic-primary",
#   "will-mikie-sherrill-win-nj-governor-dem-primary-by-15",
#   "moldova-parliamentary-election",
#   "panama-presidential-election-winner",
#   "ireland-presidential-election",
#   "will-any-candidate-win-outright-in-1st-round-of-romanian-election",
#   "south-korea-presidential-election-2nd-place",
#   "cameroon-presidential-election",
#   "seychelles-presidential-election",
#   "poland-presidential-election-margin-of-victory",
#   "south-korea-presidential-election-margin-of-victory",
#   "next-prime-minister-of-norway",
#   "norway-parliamentary-election-winner",
#   "will-peter-dutton-lose-his-seat",
#   "will-anthony-albanese-lose-his-seat",
#   "eu-election-which-party-will-win-the-most-seats",
#   "germany-eu-election",
#   "poland-eu-election",
#   "which-party-wins-second-most-seats-in-uk-election",
#   "australia-election-seat-of-brisbane",
#   "australia-election-seat-of-bennelong",
#   "singapore-parliamentary-election-winner",
#   "washington-dc-presidential-election-winner",
#   "lee-jae-myung-of-vote-in-south-korea-election-2-brackets",
#   "which-cities-provinces-will-lee-jae-myung-win",
#   "how-many-seats-will-the-lib-dems-win-in-uk-election",
#   "next-senate-majority-leader",
#   "arizona-senate-election-margin-of-victory",
#   "next-republican-house-conference-chair",
# ]

	event_slugs = [
	"nevada-us-senate-election-winner"
	]

	# fetch_and_store_all_metadata(event_slugs)
	fetch_and_store_all_trades(event_slugs)
	# fetch_and_store_all_prices(event_slugs)

