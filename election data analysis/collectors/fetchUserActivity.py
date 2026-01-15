import requests
import time
import csv
from typing import List, Dict, Any, Optional

DATA_BASE = "https://data-api.polymarket.com"

def fetch_user_activity(
    wallet: str,
    condition_id: Optional[str] = None,
    limit: int = 500,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    GET /activity via Data API. Returns user-level on-chain activity (trades, etc.),
    optionally filtered by market (conditionId).
    """
    all_act: List[Dict[str, Any]] = []
    count = 0
    while True:
        params = {
            "user": wallet,
            "limit": limit,
            "offset": offset
        }
        if condition_id:
            params["market"] = condition_id
        url = f"{DATA_BASE}/activity"
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        all_act.extend(batch)
        offset += len(batch)
        count += 1
        if count >= 40:
            break   
        # throttle a bit to avoid rate limit
        time.sleep(0.1)
    return all_act

def write_activity_to_csv(rows: List[Dict[str, Any]], filename: str):
    if not rows:
        print("No activity rows to write.")
        return
    # determine CSV headers (fields)
    fieldnames = list(rows[0].keys())
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

def main():
    wallet_addr = "0x551e72eda42a5ab39d6d78239a1d9bbb5db6b0e0"
    # you can optionally specify a market / conditionId to filter
    condition = None  # e.g. "0x…"
    activity = fetch_user_activity(wallet_addr, condition)
    print(f"Fetched {len(activity)} activity records for user {wallet_addr}")
    output_csv = f"user_activity_{wallet_addr}.csv"
    write_activity_to_csv(activity, output_csv)
    print("Wrote CSV to", output_csv)

if __name__ == "__main__":
    main()
