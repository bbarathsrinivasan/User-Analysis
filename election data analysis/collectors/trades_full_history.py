"""
Fetch full trade history for an event by combining archived monthly dumps with the
current /trades API window, streaming to per-market CSVs to avoid high memory use.

Usage (example):
    python trades_full_history.py --event-slug nevada-us-senate-election-winner \
        --archive-url https://your-bucket/trades-2024-04.csv.gz \
        --archive-url https://your-bucket/trades-2024-05.csv.gz

Notes:
- You must supply archive URLs or file paths that contain historical trades with a
  `conditionId` column. The script filters rows for markets in the event.
- Live fetching still uses the Polymarket /trades endpoint to append the recent
  window; the API itself does not expose full history.
- Output CSVs are written to data/<event_slug>/trades/<market_slug>_trades.csv
- Streaming, no large in-memory accumulation; optional dedup by transactionHash
  can be enabled (stores hashes in memory per market).
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import gzip
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import aiohttp

# Reuse collectors utilities
try:
    from polymarket_pipeline.collectors import dataCollectionScript as dcs  # type: ignore
except Exception:  # pragma: no cover - fallback for direct script run
    import importlib.util

    mod_path = Path(__file__).parent / "dataCollectionScript.py"
    spec = importlib.util.spec_from_file_location("dataCollectionScript", str(mod_path))
    if not spec or not spec.loader:
        raise ImportError("Unable to import dataCollectionScript")
    dcs = importlib.util.module_from_spec(spec)  # type: ignore
    sys.modules["dataCollectionScript"] = dcs  # type: ignore
    spec.loader.exec_module(dcs)  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"


def ensure_trades_dir(event_slug: str) -> Path:
    trades_dir = DATA_ROOT / event_slug / "trades"
    trades_dir.mkdir(parents=True, exist_ok=True)
    return trades_dir


def open_writer(path: Path, fieldnames: Iterable[str]):
    file_exists = path.exists()
    f = path.open("a" if file_exists else "w", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
    return f, writer


async def download_to_temp(session: aiohttp.ClientSession, url: str) -> Path:
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=Path(url).name)
    os.close(tmp_fd)
    out_path = Path(tmp_path)
    async with session.get(url) as resp:
        resp.raise_for_status()
        with out_path.open("wb") as f:
            async for chunk in resp.content.iter_chunked(1024 * 1024):
                f.write(chunk)
    return out_path


def iter_rows_from_file(path: Path) -> Iterable[Dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


async def process_archive(
    session: aiohttp.ClientSession,
    source: str,
    condition_to_slug: Dict[str, str],
    writers_cache: Dict[str, csv.DictWriter],
    files_cache: Dict[str, any],
    counts: Dict[str, int],
):
    # Handle http(s) URLs or local file paths
    local_path: Optional[Path]
    if source.startswith("http://") or source.startswith("https://"):
        local_path = await download_to_temp(session, source)
        cleanup = True
    else:
        local_path = Path(source)
        cleanup = False

    try:
        for row in iter_rows_from_file(local_path):
            cond = row.get("conditionId")
            if cond not in condition_to_slug:
                continue
            slug = condition_to_slug[cond]
            if slug not in writers_cache:
                f, w = open_writer(files_cache["__dir__"] / f"{slug}_trades.csv", row.keys())
                writers_cache[slug] = w
                files_cache[slug] = f
            writers_cache[slug].writerow(row)
            counts[slug] = counts.get(slug, 0) + 1
    finally:
        for slug, f in list(files_cache.items()):
            if slug == "__dir__":
                continue
            f.flush()
        if cleanup and local_path and local_path.exists():
            local_path.unlink()


async def append_live_window(
    session: aiohttp.ClientSession,
    condition_to_slug: Dict[str, str],
    trades_dir: Path,
    writers_cache: Dict[str, csv.DictWriter],
    files_cache: Dict[str, any],
    counts: Dict[str, int],
    dedup_by_tx: bool = True,
):
    seen_hashes: Dict[str, set] = {slug: set() for slug in condition_to_slug.values()} if dedup_by_tx else {}

    async def handle_market(cond: str, slug: str):
        async for batch in dcs.iter_trades_batches(session, cond):  # type: ignore[attr-defined]
            if not batch:
                continue
            # lazily open writer matching batch fields
            if slug not in writers_cache:
                f, w = open_writer(trades_dir / f"{slug}_trades.csv", batch[0].keys())
                writers_cache[slug] = w
                files_cache[slug] = f
            if dedup_by_tx:
                tx_field = "transactionHash"
                filtered = []
                for row in batch:
                    tx = row.get(tx_field)
                    if tx and tx in seen_hashes[slug]:
                        continue
                    if tx:
                        seen_hashes[slug].add(tx)
                    filtered.append(row)
                batch = filtered
            if batch:
                writers_cache[slug].writerows(batch)
                counts[slug] = counts.get(slug, 0) + len(batch)
                if slug in files_cache and files_cache[slug]:
                    files_cache[slug].flush()

    await asyncio.gather(*(handle_market(cond, slug) for cond, slug in condition_to_slug.items()))


async def main_async(event_slug: str, archive_sources: List[str]):
    trades_dir = ensure_trades_dir(event_slug)
    # load event markets
    async with aiohttp.ClientSession() as session:
        event = await dcs.get_event_by_slug(session, event_slug)  # type: ignore[attr-defined]
        markets = event.get("markets", [])
        condition_to_slug = {
            m.get("conditionId"): m.get("slug")
            for m in markets
            if m.get("conditionId") and m.get("slug")
        }
        writers_cache: Dict[str, csv.DictWriter] = {}
        files_cache: Dict[str, any] = {"__dir__": trades_dir}
        counts: Dict[str, int] = {}

        if archive_sources:
            for src in archive_sources:
                print(f"[archive] processing {src}")
                await process_archive(session, src, condition_to_slug, writers_cache, files_cache, counts)

        print("[live] fetching recent window via /trades")
        await append_live_window(session, condition_to_slug, trades_dir, writers_cache, files_cache, counts)

        # close open files
        for slug, f in list(files_cache.items()):
            if slug == "__dir__":
                continue
            f.close()

        for slug, n in counts.items():
            print(f"{slug}: {n} rows written")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch full trade history for an event")
    p.add_argument("--event-slug", required=True, help="Event slug")
    p.add_argument(
        "--archive-url",
        action="append",
        default=[],
        help="Archive URL or local path (can be repeated). Must include conditionId column.",
    )
    return p.parse_args()


def main():
    args = parse_args()
    asyncio.run(main_async(args.event_slug, args.archive_url))


if __name__ == "__main__":
    main()