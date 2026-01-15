#!/usr/bin/env python3
"""
Build per-market, per-user position files for segment analysis from data folder.

For wisconsin-us-senate-election-winner event only.

Outputs to: election data analysis/output/segment_positions/
"""

import os
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime
import pandas as pd

# Add parent directory to path to access data folder
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

# Data is in the same directory as the script
RAW_BASE = Path(__file__).parent / "data"
OUTPUT_BASE = Path(__file__).parent / "output" / "segment_positions"
TARGET_EVENT = "wisconsin-us-senate-election-winner"

# Setup logging
def log(message: str, level: str = "INFO"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def log_progress(current: int, total: int, item: str = "item"):
    """Log progress with percentage."""
    percentage = (current / total * 100) if total > 0 else 0
    remaining = total - current
    log(f"Progress: {current}/{total} {item}(s) ({percentage:.1f}%) - {remaining} remaining", "PROGRESS")


# ---------- Helpers to load and normalize trades ----------

def load_market_trades(event_id: str, market_slug: str) -> pd.DataFrame:
    """Load raw trades for a single market and normalize columns."""
    trades_path = RAW_BASE / event_id / "trades" / f"{market_slug}_trades.csv"
    if not trades_path.exists():
        raise FileNotFoundError(f"Trades file not found: {trades_path}")

    log(f"Loading trades from: {trades_path.name}")
    df = pd.read_csv(trades_path, low_memory=False)

    # Basic column mapping
    mapped = pd.DataFrame()
    mapped["user_id"] = df["proxyWallet"]
    mapped["side"] = df["side"].str.upper()
    mapped["quantity"] = pd.to_numeric(df["size"], errors="coerce")
    mapped["unix_timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce").astype("Int64")
    mapped["event_id"] = df["eventSlug"]
    mapped["market_slug"] = df["slug"]
    mapped["token_type"] = df["outcome"].str.upper()  # "YES"/"NO"

    # Trade-level price (if present)
    if "price" in df.columns:
        mapped["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Drop invalid quantities / timestamps
    initial_count = len(mapped)
    mapped = mapped.dropna(subset=["quantity", "unix_timestamp"])
    mapped["quantity"] = mapped["quantity"].astype(float)
    mapped["unix_timestamp"] = mapped["unix_timestamp"].astype(int)
    
    valid_count = len(mapped)
    if initial_count != valid_count:
        log(f"Filtered {initial_count - valid_count} invalid rows", "WARNING")

    # Convert to UTC date
    mapped["datetime"] = pd.to_datetime(mapped["unix_timestamp"], unit="s", utc=True)
    mapped["date"] = mapped["datetime"].dt.date

    log(f"Loaded {valid_count} valid trades")
    return mapped


def compute_day_offset_per_market(df: pd.DataFrame) -> pd.DataFrame:
    """Compute day_offset within ONE market: last trading date = 0, earlier days negative."""
    df = df.copy()
    max_date = df["date"].max()
    df["day_offset"] = (pd.to_datetime(df["date"]) - pd.to_datetime(max_date)).dt.days
    return df


def load_daily_closing_prices(event_id: str, market_slug: str) -> Optional[pd.DataFrame]:
    """Load daily YES/NO closing prices for a market."""
    # Try closing_prices.csv first
    prices_path = RAW_BASE / event_id / "prices" / f"{market_slug}_closing_prices.csv"
    if not prices_path.exists():
        # Try price.csv as fallback
        prices_path = RAW_BASE / event_id / "prices" / f"{market_slug}_price.csv"
        if not prices_path.exists():
            return None

    try:
        df = pd.read_csv(prices_path, low_memory=False)
    except Exception as e:
        log(f"Error loading prices: {e}", "WARNING")
        return None

    if df.empty:
        return None

    # Check if it's a closing_prices format (date, token_type, price/closing_price)
    if "date" in df.columns and "token_type" in df.columns:
        price_col = "closing_price" if "closing_price" in df.columns else "price"
        if price_col not in df.columns:
            return None
            
        df["date"] = pd.to_datetime(df["date"]).dt.date
        pivot = df.pivot_table(
            index="date",
            columns="token_type",
            values=price_col,
            aggfunc="last",
        ).reset_index()

        out = pd.DataFrame()
        out["date"] = pivot["date"]
        out["yes_token_price"] = pivot.get("YES")
        out["no_token_price"] = pivot.get("NO")

        out = out.sort_values("date").reset_index(drop=True)
        out["yes_token_price"] = out["yes_token_price"].ffill()
        out["no_token_price"] = out["no_token_price"].ffill()

        return out
    elif "timestamp" in df.columns and "token_id" in df.columns and "price" in df.columns:
        # Price format with token_id
        trades_path = RAW_BASE / event_id / "trades" / f"{market_slug}_trades.csv"
        token_id_to_type = {}
        
        if trades_path.exists():
            try:
                trades_df = pd.read_csv(trades_path, low_memory=False)
                if 'asset' in trades_df.columns and 'outcome' in trades_df.columns:
                    for _, row in trades_df[['asset', 'outcome']].drop_duplicates().iterrows():
                        token_id = str(row['asset'])
                        outcome = str(row['outcome']).upper()
                        if outcome in ['YES', 'NO']:
                            token_id_to_type[token_id] = outcome
            except Exception:
                pass
        
        if not token_id_to_type:
            unique_token_ids = df['token_id'].drop_duplicates().tolist()
            if len(unique_token_ids) >= 1:
                token_id_to_type[str(unique_token_ids[0])] = 'YES'
            if len(unique_token_ids) >= 2:
                token_id_to_type[str(unique_token_ids[1])] = 'NO'
        
        df['token_type'] = df['token_id'].astype(str).map(token_id_to_type)
        df = df[df['token_type'].notna()].copy()
        
        if df.empty:
            return None
        
        df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
        df['date'] = df['datetime'].dt.date
        
        df = df.sort_values('timestamp')
        daily_closing = df.groupby(['date', 'token_type']).last().reset_index()
        
        pivot = daily_closing.pivot_table(
            index="date",
            columns="token_type",
            values="price",
            aggfunc="last",
        ).reset_index()

        out = pd.DataFrame()
        out["date"] = pivot["date"]
        out["yes_token_price"] = pivot.get("YES")
        out["no_token_price"] = pivot.get("NO")

        out = out.sort_values("date").reset_index(drop=True)
        out["yes_token_price"] = out["yes_token_price"].ffill()
        out["no_token_price"] = out["no_token_price"].ffill()

        return out
    else:
        return None


def derive_daily_prices_from_trades(trades_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Derive daily YES/NO prices from raw trades when dedicated closing price files are missing."""
    if "price" not in trades_df.columns:
        return None

    df = trades_df.copy()
    if "date" not in df.columns or "token_type" not in df.columns:
        return None

    df_sorted = df.sort_values(["date", "token_type", "unix_timestamp"])
    last_per_bucket = (
        df_sorted.groupby(["date", "token_type"], as_index=False)
        .tail(1)[["date", "token_type", "price"]]
    )

    if last_per_bucket.empty:
        return None

    last_per_bucket["date"] = pd.to_datetime(last_per_bucket["date"]).dt.date

    pivot = last_per_bucket.pivot_table(
        index="date",
        columns="token_type",
        values="price",
        aggfunc="last",
    ).reset_index()

    out = pd.DataFrame()
    out["date"] = pivot["date"]
    out["yes_token_price"] = pivot.get("YES")
    out["no_token_price"] = pivot.get("NO")

    out = out.sort_values("date").reset_index(drop=True)
    out["yes_token_price"] = out["yes_token_price"].ffill()
    out["no_token_price"] = out["no_token_price"].ffill()

    return out


# ---------- Core per-market, per-user aggregation ----------

def build_daily_user_token_series(df: pd.DataFrame) -> pd.DataFrame:
    """From raw trades, build per-user, per-token_type, per-day_offset daily series."""
    df = compute_day_offset_per_market(df)

    buys = df[df["side"] == "BUY"].groupby(
        ["user_id", "token_type", "day_offset"], as_index=False
    ).agg(daily_buy=("quantity", "sum"))

    sells = df[df["side"] == "SELL"].groupby(
        ["user_id", "token_type", "day_offset"], as_index=False
    ).agg(daily_sell=("quantity", "sum"))

    eod = df.groupby(["user_id", "token_type", "day_offset"], as_index=False).agg(
        timestamp=("unix_timestamp", "max"),
        date=("date", "first"),
    )

    out = eod.merge(buys, on=["user_id", "token_type", "day_offset"], how="left")
    out = out.merge(sells, on=["user_id", "token_type", "day_offset"], how="left")

    out["daily_buy"] = out["daily_buy"].fillna(0.0)
    out["daily_sell"] = out["daily_sell"].fillna(0.0)
    out["net_tokens"] = out["daily_buy"] - out["daily_sell"]

    return out


def build_per_user_market_df(
    event_id: str,
    market_slug: str,
    daily_df: pd.DataFrame,
    prices_df: Optional[pd.DataFrame],
    user_id: str,
) -> pd.DataFrame:
    """For a single user & single market, build the requested output DataFrame."""
    user_tok = daily_df[daily_df["user_id"] == user_id].copy()
    if user_tok.empty:
        return pd.DataFrame()

    yes_df = user_tok[user_tok["token_type"] == "YES"].copy()
    no_df = user_tok[user_tok["token_type"] == "NO"].copy()

    user_offsets = sorted(set(yes_df["day_offset"]).union(no_df["day_offset"]))
    if not user_offsets:
        return pd.DataFrame()

    first_user_day = min(user_offsets)
    closing_day = 0
    max_date = daily_df["date"].max()
    
    market_day_info = daily_df.groupby("day_offset", as_index=False).agg(
        date=("date", "first"),
        timestamp=("timestamp", "max"),
    )
    offset_to_info = {
        row["day_offset"]: {"date": row["date"], "timestamp": int(row["timestamp"])}
        for _, row in market_day_info.iterrows()
    }

    all_day_offsets = list(range(first_user_day, closing_day + 1))

    rows = []
    for day_offset in all_day_offsets:
        d = (pd.to_datetime(max_date) + pd.Timedelta(days=day_offset)).date()
        
        if day_offset in offset_to_info:
            ts = offset_to_info[day_offset]["timestamp"]
        else:
            ts = int(pd.Timestamp(d).replace(hour=23, minute=59, second=59).timestamp())

        yes_row = yes_df[yes_df["day_offset"] == day_offset]
        no_row = no_df[no_df["day_offset"] == day_offset]

        yes_daily_buy = float(yes_row.iloc[0]["daily_buy"]) if not yes_row.empty else 0.0
        yes_daily_sell = float(yes_row.iloc[0]["daily_sell"]) if not yes_row.empty else 0.0
        yes_net = float(yes_row.iloc[0]["net_tokens"]) if not yes_row.empty else 0.0

        no_daily_buy = float(no_row.iloc[0]["daily_buy"]) if not no_row.empty else 0.0
        no_daily_sell = float(no_row.iloc[0]["daily_sell"]) if not no_row.empty else 0.0
        no_net = float(no_row.iloc[0]["net_tokens"]) if not no_row.empty else 0.0

        rows.append({
            "day_offset": int(day_offset),
            "timestamp": ts,
            "date": d,
            "yes_daily_buy": yes_daily_buy,
            "yes_daily_sell": yes_daily_sell,
            "yes_net_tokens": yes_net,
            "no_daily_buy": no_daily_buy,
            "no_daily_sell": no_daily_sell,
            "no_net_tokens": no_net,
        })

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows).sort_values("day_offset").reset_index(drop=True)

    out["yes_cumulative_position"] = out["yes_net_tokens"].cumsum()
    out["no_cumulative_position"] = out["no_net_tokens"].cumsum()
    out["H_y"] = out["yes_cumulative_position"]
    out["H_n"] = out["no_cumulative_position"]

    def _pos_yes(row):
        H_y, H_n = row["H_y"], row["H_n"]
        val = 0.0
        if H_y > 0:
            val += H_y
        if H_n < 0:
            val += -H_n
        return val

    def _pos_no(row):
        H_y, H_n = row["H_y"], row["H_n"]
        val = 0.0
        if H_n > 0:
            val += H_n
        if H_y < 0:
            val += -H_y
        return val

    out["individual_yes_position"] = out.apply(_pos_yes, axis=1)
    out["individual_no_position"] = out.apply(_pos_no, axis=1)

    out = out[[
        "day_offset", "timestamp", "date",
        "yes_daily_buy", "yes_daily_sell", "yes_net_tokens", "yes_cumulative_position",
        "no_daily_buy", "no_daily_sell", "no_net_tokens", "no_cumulative_position",
        "H_y", "H_n", "individual_yes_position", "individual_no_position",
    ]]

    return out


# ---------- Main orchestration ----------

def process_market(event_id: str, market_slug: str, market_num: int, total_markets: int) -> None:
    """Process a single market with progress tracking."""
    log(f"[Market {market_num}/{total_markets}] Processing: {market_slug}")
    start_time = datetime.now()
    
    try:
        trades_df = load_market_trades(event_id, market_slug)
        if trades_df.empty:
            log("  No trades found, skipping.", "WARNING")
            return

        daily_df = build_daily_user_token_series(trades_df)
        daily_df["event_id"] = event_id
        daily_df["market_slug"] = market_slug

        prices_df = load_daily_closing_prices(event_id, market_slug)
        if prices_df is None:
            log("  No price file found, deriving from trades", "INFO")
            prices_df = derive_daily_prices_from_trades(trades_df)

        user_ids = daily_df["user_id"].unique()
        total_users = len(user_ids)
        log(f"  Found {total_users} user(s) in this market")

        user_dir = OUTPUT_BASE / event_id / market_slug
        user_dir.mkdir(parents=True, exist_ok=True)

        processed_users = 0
        for user_idx, user_id in enumerate(user_ids, 1):
            user_out = build_per_user_market_df(event_id, market_slug, daily_df, prices_df, user_id)
            if user_out.empty:
                continue

            out_path = user_dir / f"user_{user_id}.csv"
            user_out.to_csv(out_path, index=False)
            processed_users += 1
            
            # Log every 50 users or at the end
            if user_idx % 50 == 0 or user_idx == total_users:
                log(f"  Processed {user_idx}/{total_users} users ({processed_users} with data)", "PROGRESS")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        log(f"  ✓ Completed in {elapsed:.1f}s - Saved {processed_users} user files", "SUCCESS")
        
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        log(f"  ✗ ERROR after {elapsed:.1f}s: {e}", "ERROR")
        raise


def main():
    log("=" * 80)
    log("Building per-market, per-user segment output from data folder")
    log(f"Target Event: {TARGET_EVENT}")
    log("=" * 80)

    if not RAW_BASE.exists():
        log(f"Data base directory not found: {RAW_BASE}", "ERROR")
        return

    event_dir = RAW_BASE / TARGET_EVENT
    if not event_dir.exists():
        log(f"Event directory not found: {event_dir}", "ERROR")
        return

    trades_dir = event_dir / "trades"
    if not trades_dir.exists():
        log(f"Trades directory not found: {trades_dir}", "ERROR")
        return

    trade_files = sorted(trades_dir.glob("*_trades.csv"))
    if not trade_files:
        log(f"No trade files found in {trades_dir}", "ERROR")
        return

    total_markets = len(trade_files)
    log(f"\nFound {total_markets} market(s) to process")
    log(f"Output directory: {OUTPUT_BASE}")
    log("-" * 80)

    overall_start = datetime.now()
    
    for market_idx, trade_file in enumerate(trade_files, 1):
        market_slug = trade_file.stem.replace("_trades", "")
        process_market(TARGET_EVENT, market_slug, market_idx, total_markets)
        
        if market_idx < total_markets:
            log_progress(market_idx, total_markets, "market")
            log("")

    overall_elapsed = (datetime.now() - overall_start).total_seconds()
    log("=" * 80)
    log(f"✓ All markets processed successfully in {overall_elapsed:.1f} seconds")
    log(f"Output written to: {OUTPUT_BASE}")
    log("=" * 80)


if __name__ == "__main__":
    main()



