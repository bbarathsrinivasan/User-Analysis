# import requests
# import time
# import csv
# from typing import Dict, List, Any, Optional

# # Base URLs (public)
# GAMMA_BASE = "https://gamma-api.polymarket.com"
# DATA_BASE = "https://data-api.polymarket.com"

# # === Helper / API wrappers ===

# def get_event_by_slug(event_slug: str) -> Dict[str, Any]:
#     """
#     GET /events/slug/{slug} via Gamma API.
#     Returns event object including `markets` list.
#     """
#     url = f"{GAMMA_BASE}/events/slug/{event_slug}"
#     resp = requests.get(url)
#     resp.raise_for_status()
#     ev = resp.json()
#     return ev

# def get_market_info_by_slug(market_slug: str) -> Dict[str, Any]:
#     """
#     GET /markets/slug/{slug} via Gamma API.
#     Returns metadata for the specific market.
#     """
#     url = f"{GAMMA_BASE}/markets/slug/{market_slug}"
#     resp = requests.get(url)
#     resp.raise_for_status()
#     return resp.json()

# def fetch_trades_for_market(condition_id: str, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
#     """
#     Uses Data API GET /trades with `market` param filtering by conditionId.
#     Returns list of trades. Paginates by offset.
#     """
#     all_trades = []
#     while True:
#         params = {
#             "market": condition_id,
#             "limit": limit,
#             "offset": offset
#         }
#         url = f"{DATA_BASE}/trades"
#         resp = requests.get(url, params=params)
#         resp.raise_for_status()
#         batch = resp.json()
#         if not batch:
#             break
#         all_trades.extend(batch)
#         offset += len(batch)
#         # throttle to avoid Data API rate limit (75 req / 10s for /trades)  [oai_citation:0‡Polymarket](https://docs.polymarket.com/quickstart/introduction/rate-limits?utm_source=chatgpt.com)
#         time.sleep(0.15)
#     return all_trades

# def fetch_user_activity(wallet: str, condition_id: Optional[str] = None, limit: int = 500, offset: int = 0) -> List[Dict[str, Any]]:
#     """
#     GET /activity via Data API. Returns user-level on-chain activity (trades, etc.), optionally filtered by market.
#     """
#     all_act = []
#     while True:
#         params = {
#             "user": wallet,
#             "limit": limit,
#             "offset": offset
#         }
#         if condition_id:
#             params["market"] = condition_id
#         url = f"{DATA_BASE}/activity"
#         resp = requests.get(url, params=params)
#         resp.raise_for_status()
#         batch = resp.json()
#         if not batch:
#             break
#         all_act.extend(batch)
#         offset += len(batch)
#         # small throttle
#         time.sleep(0.1)
#     return all_act

# def save_list_of_dicts_to_csv(rows: List[Dict[str, Any]], filename: str):
#     if not rows:
#         print("No rows to save for", filename)
#         return
#     with open(filename, "w", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
#         writer.writeheader()
#         for r in rows:
#             writer.writerow(r)

# # === Main orchestration ===

# def fetch_event_markets_trades(event_slug: str, save: bool = True):
#     """
#     Given an event slug, fetch its markets, and for each market fetch trade history.
#     Optionally save CSV per market.
#     Returns dict: market_slug -> {metadata, trades}
#     """
#     event = get_event_by_slug(event_slug)
#     print("Fetched event:", event.get("title"), "with slug:", event.get("slug"))
#     markets = event.get("markets", [])
#     result = {}
#     for m in markets:
#         m_slug = m.get("slug")
#         cond_id = m.get("conditionId")
#         print("Processing market:", m_slug, cond_id)
#         # fetch metadata (optional, extra detail) via Gamma
#         meta = get_market_info_by_slug(m_slug)
#         # fetch trades via Data API
#         trades = fetch_trades_for_market(cond_id)
#         print(f" --> {len(trades)} trades fetched for market {m_slug}")
#         result[m_slug] = {
#             "metadata": meta,
#             "trades": trades
#         }
#         if save:
#             save_list_of_dicts_to_csv(trades, f"{event_slug}__{m_slug}_trades.csv")
#     return result

# # Example usage
# if __name__ == "__main__":
#     slug = "who-will-trump-fire-in-first-100-days"  # event slug example
#     data = fetch_event_markets_trades(slug)
#     print(f"Fetched data for {len(data)} markets in event {slug}.")
#     print(f"data: {data['will-trump-say-border-5-times-during-ballroom-dinner-on-october-15']}")
#     userData = fetch_user_activity("0x203ae68d1fdf003af6da47dce6fe89a3351eada4")
#     print(f"Fetched {len(userData)} activity records for user.")
#     # `data` is a dict by market slug with trade lists & metadata

import asyncio
import aiohttp
import time
import csv
from pathlib import Path
from typing import Dict, List, Any, AsyncIterator

# Base URLs
GAMMA_BASE = "https://gamma-api.polymarket.com"
DATA_BASE = "https://data-api.polymarket.com"

# Rate limits from Polymarket docs (as of Aug 2025):
# Data API /trades → 200 requests / 10s
# IMPORTANT: limit max is 500, offset max is 1,000 (only get first 1,500 trades with offset!)
# Solution: Use time-based pagination with 'before' parameter
class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls: List[float] = []
    
    async def wait_for_slot(self):
        now = time.monotonic()
        cutoff = now - self.period
        # drop outdated calls
        while self.calls and self.calls[0] < cutoff:
            self.calls.pop(0)
        if len(self.calls) >= self.max_calls:
            earliest = self.calls[0]
            await asyncio.sleep((earliest + self.period) - now + 0.01)
        self.calls.append(time.monotonic())

trades_limiter = RateLimiter(200, 10.0)  # Updated to 200 req/10s

async def fetch_json(session: aiohttp.ClientSession, url: str, params: dict = None, retries: int = 5) -> Any:
    for attempt in range(retries):
        try:
            timeout = aiohttp.ClientTimeout(total=60)  # Increased to 60 seconds
            async with session.get(url, params=params, timeout=timeout) as resp:
                if resp.status == 429:
                    # rate limit, back off exponentially
                    wait_time = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
                    print(f"[fetch_json] Rate limited (429), waiting {wait_time}s before retry {attempt + 1}/{retries}")
                    await asyncio.sleep(wait_time)
                    continue
                resp.raise_for_status()
                return await resp.json()
        except asyncio.TimeoutError:
            print(f"[fetch_json] Timeout on attempt {attempt + 1}/{retries}, retrying...")
            await asyncio.sleep(2 * (attempt + 1))
            continue
        except Exception as e:
            print(f"[fetch_json] Error on attempt {attempt + 1}/{retries}: {type(e).__name__}: {e}")
            await asyncio.sleep(2 * (attempt + 1))
            continue
    raise RuntimeError(f"Failed to fetch {url} after {retries} tries")

async def get_event_by_slug(session: aiohttp.ClientSession, event_slug: str) -> Dict[str, Any]:
    url = f"{GAMMA_BASE}/events/slug/{event_slug}"
    return await fetch_json(session, url)

async def get_market_info_by_slug(session: aiohttp.ClientSession, market_slug: str) -> Dict[str, Any]:
    url = f"{GAMMA_BASE}/markets/slug/{market_slug}"
    return await fetch_json(session, url)

# async def fetch_trades_for_market(session: aiohttp.ClientSession, condition_id: str, limit: int = 500, offset: int = 0) -> List[Dict[str, Any]]:
#     trades = []
#     count = 0
#     total_fetched = 0
#     while True:
#         # Rate limit
#         await trades_limiter.wait_for_slot()
#         params = {"market": condition_id, "limit": limit, "offset": offset}
#         url = f"{DATA_BASE}/trades"
#         batch = await fetch_json(session, url, params=params)
#         if not batch:
#             break
#         trades.extend(batch)
#         total_fetched += len(batch)
#         # Log progress every 10 pages or when starting
#         if count % 10 == 0 or count == 0:
#             print(f"[fetch_trades] condition_id={condition_id[:20]}... | page={count+1} | total_trades={total_fetched} | batch_size={len(batch)}")
#         # If we got less than `limit`, no more pages
#         if len(batch) < limit:
#             break
#         offset += len(batch)
#         count+=1
#         if count >= 2000:
#             break
#         # continue to next page
#     print(f"[fetch_trades] condition_id={condition_id[:20]}... | COMPLETED | total_pages={count+1} | total_trades={total_fetched}")
#     return trades

async def iter_trades_batches(
    session: aiohttp.ClientSession,
    condition_id: str,
    limit: int = 500,  # API max is 500 (as of Aug 2025)
    offset: int = 0,
    max_trades: int | None = None,
) -> AsyncIterator[List[Dict[str, Any]]]:
    """
    Stream trades in batches without accumulating them all in memory.
    Yields each batch as a list of dicts.
    
    CRITICAL: As of Aug 2025, Polymarket API limits:
    - Max limit: 500 trades per request
    - Max offset: 1,000 (only allows first 1,500 trades with offset!)
    
    Solution: Uses TIME-BASED pagination with 'before' parameter to fetch ALL trades.
    Trades are ordered newest-first, we use timestamp of oldest trade as 'before' cursor.
    """
    count = 0
    total_fetched = 0
    before_timestamp = None  # For time-based pagination
    
    while True:
        await trades_limiter.wait_for_slot()
        
        # Build params - use time-based pagination after offset limit
        params = {"market": condition_id, "limit": limit}
        
        if before_timestamp is not None:
            # Time-based pagination: fetch trades before this timestamp
            params["before"] = before_timestamp
        elif offset > 0 and offset <= 1000:
            # Offset pagination (only for first 1,500 trades)
            params["offset"] = offset
        # else: first request, no pagination params
        
        url = f"{DATA_BASE}/trades"
        batch = await fetch_json(session, url, params=params)
        
        if not batch:
            if count == 0:
                print(f"[fetch_trades] condition_id={condition_id[:20]}... | No trades found")
            else:
                print(f"[fetch_trades] condition_id={condition_id[:20]}... | Empty batch, end of data")
            break
        
        batch_size = len(batch)
        total_fetched += batch_size
        
        # Extract timestamp of oldest trade in this batch for next iteration
        # Trades are ordered newest-first, so last trade is oldest
        if batch and "timestamp" in batch[-1]:
            oldest_timestamp = batch[-1]["timestamp"]
            before_timestamp = oldest_timestamp
        
        if max_trades is not None and total_fetched > max_trades:
            # trim the last batch to respect the cap
            excess = total_fetched - max_trades
            if excess > 0:
                batch = batch[:-excess] if excess <= len(batch) else []
                total_fetched -= excess
            if not batch:
                break
        
        if count % 10 == 0 or count == 0:
            pagination_info = f"before={before_timestamp}" if before_timestamp else f"offset={offset}"
            print(
                f"[fetch_trades] condition_id={condition_id[:20]}... | "
                f"page={count+1} | total_trades={total_fetched:,} | batch_size={batch_size} | {pagination_info}"
            )
        
        yield batch
        
        # Update offset for initial pages (before switching to time-based)
        if before_timestamp is None:
            offset += batch_size
        
        count += 1
        
        # If we got less than the limit, we've reached the end
        if batch_size < limit:
            print(f"[fetch_trades] Received partial batch ({batch_size} < {limit}), end of data reached")
            break
        
        if max_trades is not None and total_fetched >= max_trades:
            break
    
    print(
        f"[fetch_trades] condition_id={condition_id[:20]}... | COMPLETED | "
        f"total_pages={count} | total_trades={total_fetched:,}"
    )


async def fetch_trades_for_market(session: aiohttp.ClientSession, condition_id: str, limit: int = 500, offset: int = 0, max_trades: int | None = None) -> List[Dict[str, Any]]:
    """
    Backward-compatible wrapper to fetch all trades (still accumulates).
    Prefer `iter_trades_batches` for streaming.
    
    WARNING: This accumulates all trades in memory. For large markets (millions of trades),
    use iter_trades_batches instead to avoid memory issues.
    
    Uses time-based pagination to bypass the offset=1000 limit.
    """
    trades: List[Dict[str, Any]] = []
    async for batch in iter_trades_batches(session, condition_id, limit=limit, offset=offset, max_trades=max_trades):
        trades.extend(batch)
    return trades


async def worker_fetch_and_save(session: aiohttp.ClientSession, market_slug: str, cond_id: str, out_dir: str, max_trades: int | None = None):
    """Fetch trades for a market and stream-write them to CSV to avoid high memory usage."""
    meta = await get_market_info_by_slug(session, market_slug)
    fname = f"{out_dir}/{market_slug}_trades.csv"
    writer = None
    f = None
    total = 0
    try:
        async for batch in iter_trades_batches(session, cond_id, max_trades=max_trades):
            if writer is None:
                f = open(fname, "w", newline="", encoding="utf-8")
                writer = csv.DictWriter(f, fieldnames=batch[0].keys())
                writer.writeheader()
            writer.writerows(batch)
            total += len(batch)
            if f:
                f.flush()
    finally:
        if f:
            f.close()
    print(f"[{market_slug}] fetched {total} trades.")
    return {"slug": market_slug, "metadata": meta, "trades_count": total}

async def fetch_event_markets_trades(event_slug: str, out_dir: str = ".", concurrency: int = 5, max_trades: int | None = None):
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    async with aiohttp.ClientSession() as session:
        event = await get_event_by_slug(session, event_slug)
        print("Event:", event.get("title"))
        markets = event.get("markets", [])
        sem = asyncio.Semaphore(concurrency)
        tasks = []
        for m in markets:
            m_slug = m.get("slug")
            cond = m.get("conditionId")
            async def semtask(slug=m_slug, cond_id=cond):
                async with sem:
                    return await worker_fetch_and_save(session, slug, cond_id, str(out_path), max_trades=max_trades)
            tasks.append(asyncio.create_task(semtask()))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

# === Run logic (fixed values) ===

def run():
    EVENT_SLUG = "romania-presidential-election-winner"
    OUTPUT_DIR = "./output"
    CONCURRENCY = 4
    MAX_TRADES = 100  # cap per-market to 100 for quicker runs / verification
    results = asyncio.run(fetch_event_markets_trades(EVENT_SLUG, OUTPUT_DIR, CONCURRENCY, max_trades=MAX_TRADES))
    # print("Finished. Results:", results)

if __name__ == "__main__":
    run()