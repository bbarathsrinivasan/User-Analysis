from typing import Any, Dict, List
import requests
import csv
from datetime import datetime, timezone
import re
import asyncio
import aiohttp


CLOB_BASE = "https://clob.polymarket.com"
GAMMA_BASE = "https://gamma-api.polymarket.com"

def get_event_by_slug(event_slug: str) -> Dict[str, Any]:
    """
    GET /events/slug/{slug} via Gamma API.
    Returns event object including `markets` list.
    """
    url = f"{GAMMA_BASE}/events/slug/{event_slug}"
    resp = requests.get(url)
    resp.raise_for_status()
    ev = resp.json()
    return ev
def get_market_by_slug(slug: str) -> dict:
    url = f"{GAMMA_BASE}/markets/slug/{slug}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()

def iso_to_unix(iso: str) -> int:
    """Parse ISO8601 timestamps with variable fractional seconds and Z/offsets.

    Handles cases like:
      - 2024-11-26T23:40:11Z
      - 2024-11-26T23:40:11.3Z
      - 2024-11-26T23:40:11.36594Z
      - 2024-11-26T23:40:11.365940+00:00
      - 2024-11-26T23:40:11+00:00
    """
    s = iso.strip().replace("Z", "+00:00")
    # Normalize fractional seconds to at most 6 digits for Python's fromisoformat
    # Regex: split main, fraction, and tz offset
    m = re.match(r"^(.*T\d{2}:\d{2}:\d{2})(?:\.(\d+))?(.*)$", s)
    if m:
        head, frac, tail = m.groups()
        if frac is not None:
            if len(frac) > 6:
                frac = frac[:6]
            else:
                frac = frac.ljust(6, '0')
            s = f"{head}.{frac}{tail}"
    dt = datetime.fromisoformat(s)
    # Ensure timezone-aware; if missing tz, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())

def fetch_price_history(token_id: str, start_ts: int, end_ts: int) -> list:
    url = f"{CLOB_BASE}/prices-history"
    params = {
        "market": token_id,
        "interval": "max",
        "fidelity": 60,
        "startTs": start_ts
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json().get("history", [])

def write_csv(rows: list, fname: str):
    if not rows:
        print("No rows to write.")
        return
    keys = sorted(rows[0].keys())
    with open(fname, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def fetch_market_price_history(slug: str, out_csv: str):
    meta = get_market_by_slug(slug)
    print("Market:", meta.get("question"))
    # parse token ids from `clobTokenIds` field
    import json
    token_ids = json.loads(meta.get("clobTokenIds", "[]"))
    if len(token_ids) != 2:
        print("Warning: token count != 2", token_ids)
    # compute start / end timestamps
    start_iso = meta.get("startDate") or meta.get("createdAt")
    end_iso = meta.get("endDate")
    if not start_iso:
        raise RuntimeError("No start date in metadata")
    start_ts = iso_to_unix(start_iso)
    end_ts = iso_to_unix(end_iso) if end_iso else int(datetime.now(timezone.utc).timestamp())
    print("Time window:", start_ts, end_ts)
    rows = []
    for token_id in token_ids:
        hist = fetch_price_history(token_id, start_ts, end_ts)
        for rec in hist:
            rows.append({
                "market_slug": slug,
                "token_id": token_id,
                "timestamp": rec.get("t"),
                "price": rec.get("p")
            })
    write_csv(rows, out_csv)
    print("Wrote", len(rows), "rows to", out_csv)
    return rows


# Async versions for better performance
async def get_event_by_slug_async(session: aiohttp.ClientSession, event_slug: str) -> Dict[str, Any]:
    """Async version of get_event_by_slug."""
    url = f"{GAMMA_BASE}/events/slug/{event_slug}"
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()


async def get_market_by_slug_async(session: aiohttp.ClientSession, slug: str) -> Dict[str, Any]:
    """Async version of get_market_by_slug."""
    url = f"{GAMMA_BASE}/markets/slug/{slug}"
    async with session.get(url) as resp:
        resp.raise_for_status()
        return await resp.json()


async def fetch_price_history_async(session: aiohttp.ClientSession, token_id: str, start_ts: int, end_ts: int) -> List[Dict[str, Any]]:
    """Async version of fetch_price_history."""
    url = f"{CLOB_BASE}/prices-history"
    params = {
        "market": token_id,
        "interval": "max",
        "fidelity": 60,
        "startTs": start_ts
    }
    async with session.get(url, params=params) as resp:
        resp.raise_for_status()
        data = await resp.json()
        return data.get("history", [])


async def fetch_market_price_history_async(session: aiohttp.ClientSession, slug: str) -> List[Dict[str, Any]]:
    """Async version of fetch_market_price_history. Returns rows without writing CSV."""
    meta = await get_market_by_slug_async(session, slug)
    # parse token ids from `clobTokenIds` field
    import json
    token_ids = json.loads(meta.get("clobTokenIds", "[]"))
    if len(token_ids) != 2:
        print(f"Warning: token count != 2 for {slug}: {token_ids}")
    # compute start / end timestamps
    start_iso = meta.get("startDate") or meta.get("createdAt")
    end_iso = meta.get("endDate")
    if not start_iso:
        raise RuntimeError(f"No start date in metadata for {slug}")
    start_ts = iso_to_unix(start_iso)
    end_ts = iso_to_unix(end_iso) if end_iso else int(datetime.now(timezone.utc).timestamp())
    
    rows = []
    # Fetch price history for all tokens concurrently
    tasks = [fetch_price_history_async(session, token_id, start_ts, end_ts) for token_id in token_ids]
    histories = await asyncio.gather(*tasks)
    
    for token_id, hist in zip(token_ids, histories):
        for rec in hist:
            rows.append({
                "market_slug": slug,
                "token_id": token_id,
                "timestamp": rec.get("t"),
                "price": rec.get("p")
            })
    return rows

if __name__ == "__main__":
    event_slug = "belarus-presidential-election"
    event = get_event_by_slug(event_slug)
    print("Fetched event:", event.get("title"), "with slug:", event.get("slug"))
    markets = event.get("markets", [])
    result = {}
    for m in markets:
        m_slug = m.get("slug")
        cond_id = m.get("conditionId")
        slug = m_slug
        out = f"{slug}_price.csv"
        data = fetch_market_price_history(slug, out)
    print("Done")
