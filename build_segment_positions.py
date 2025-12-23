#!/usr/bin/env python3
"""
Build per-market, per-user position files for segment analysis.

For each event in raw/<event_id>/trades/*.csv and each market_slug,
this script writes:

  segment_output/<event_id>/<market_slug>/user_<user_id>.csv

Columns:
  day_offset, timestamp, date,
  yes_daily_buy, yes_daily_sell, yes_net_tokens, yes_cumulative_position,
  no_daily_buy, no_daily_sell, no_net_tokens, no_cumulative_position,
  H_y, H_n, individual_yes_position, individual_no_position
"""

import os
from pathlib import Path
from typing import Dict, Tuple, Optional

import pandas as pd


RAW_BASE = Path("raw")
OUTPUT_BASE = Path("segment_output")


# ---------- Helpers to load and normalize trades ----------

def load_market_trades(event_id: str, market_slug: str) -> pd.DataFrame:
    """
    Load raw trades for a single market and normalize columns.

    Expected raw columns in trades CSV:
      proxyWallet, side, size, timestamp, slug, eventSlug, outcome

    Returns a DataFrame with:
      user_id, side, quantity, unix_timestamp, date, event_id, market_slug, token_type
    """
    trades_path = RAW_BASE / event_id / "trades" / f"{market_slug}_trades.csv"
    if not trades_path.exists():
        raise FileNotFoundError(f"Trades file not found: {trades_path}")

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

    # Trade-level price (if present) – used later to derive daily prices
    if "price" in df.columns:
        mapped["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Drop invalid quantities / timestamps
    mapped = mapped.dropna(subset=["quantity", "unix_timestamp"])
    mapped["quantity"] = mapped["quantity"].astype(float)
    mapped["unix_timestamp"] = mapped["unix_timestamp"].astype(int)

    # Convert to UTC date
    mapped["datetime"] = pd.to_datetime(mapped["unix_timestamp"], unit="s", utc=True)
    mapped["date"] = mapped["datetime"].dt.date

    return mapped


def compute_day_offset_per_market(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute day_offset within ONE market: last trading date = 0, earlier days negative.

    df must already be filtered to a single (event_id, market_slug).
    """
    df = df.copy()
    max_date = df["date"].max()
    df["day_offset"] = (pd.to_datetime(df["date"]) - pd.to_datetime(max_date)).dt.days
    return df


# ---------- Helpers to load daily prices (assumption: use *_closing_prices.csv) ----------

def load_daily_closing_prices(event_id: str, market_slug: str) -> Optional[pd.DataFrame]:
    """
    Load daily YES/NO closing prices for a market.

    Assumes a file:
      raw/<event_id>/prices/<market_slug>_closing_prices.csv

    and that it has at least:
      date, token_type, price

    Returns a DataFrame with columns:
      date (datetime.date), yes_token_price, no_token_price
    or None if prices file is missing / unusable.
    """
    prices_path = RAW_BASE / event_id / "prices" / f"{market_slug}_closing_prices.csv"
    if not prices_path.exists():
        return None

    try:
        df = pd.read_csv(prices_path, low_memory=False)
    except Exception:
        return None

    if df.empty:
        return None

    # Expect either date+token_type+price or something compatible
    if "date" not in df.columns or "token_type" not in df.columns or "price" not in df.columns:
        # Try to infer: if timestamp+token_id etc. exist, this may need custom handling.
        return None

    # Normalize date
    df["date"] = pd.to_datetime(df["date"]).dt.date
    pivot = df.pivot_table(
        index="date",
        columns="token_type",
        values="price",
        aggfunc="last",
    ).reset_index()

    out = pd.DataFrame()
    out["date"] = pivot["date"]
    out["yes_token_price"] = pivot.get("YES")
    out["no_token_price"] = pivot.get("NO")

    # Forward fill prices by date
    out = out.sort_values("date").reset_index(drop=True)
    out["yes_token_price"] = out["yes_token_price"].ffill()
    out["no_token_price"] = out["no_token_price"].ffill()

    return out


def derive_daily_prices_from_trades(trades_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Derive daily YES/NO prices from raw trades when dedicated closing price files
    are missing or unusable.

    Strategy:
      - For each calendar date and token_type (YES/NO), take the LAST trade price
        of that day (by unix_timestamp) as the "closing" price.
      - Pivot to columns yes_token_price / no_token_price.
      - Sort by date and forward-fill missing prices so every later day has a price.
    """
    if "price" not in trades_df.columns:
        return None

    df = trades_df.copy()
    # Ensure we have date and token_type
    if "date" not in df.columns or "token_type" not in df.columns:
        return None

    # For each (date, token_type), get last trade by timestamp
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

    # Forward fill prices over time
    out = out.sort_values("date").reset_index(drop=True)
    out["yes_token_price"] = out["yes_token_price"].ffill()
    out["no_token_price"] = out["no_token_price"].ffill()

    return out


# ---------- Core per-market, per-user aggregation ----------

def build_daily_user_token_series(df: pd.DataFrame) -> pd.DataFrame:
    """
    From raw trades (one market), build per-user, per-token_type, per-day_offset daily series.

    Returns DataFrame with:
      user_id, token_type, day_offset, timestamp (EOD ts), date,
      daily_buy, daily_sell, net_tokens
    """
    # Compute day_offset first
    df = compute_day_offset_per_market(df)

    # Daily BUY/SELL quantities per (user, token_type, day_offset)
    buys = df[df["side"] == "BUY"].groupby(
        ["user_id", "token_type", "day_offset"], as_index=False
    ).agg(daily_buy=("quantity", "sum"))

    sells = df[df["side"] == "SELL"].groupby(
        ["user_id", "token_type", "day_offset"], as_index=False
    ).agg(daily_sell=("quantity", "sum"))

    # EOD timestamp & date per (user, token_type, day_offset): max ts in that bucket
    eod = df.groupby(["user_id", "token_type", "day_offset"], as_index=False).agg(
        timestamp=("unix_timestamp", "max"),
        date=("date", "first"),  # all rows in bucket are same calendar date
    )

    # Merge pieces
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
    """
    For a single user & single market, build the requested output DataFrame.
    Fills all days from user's first trade day through closing day (day_offset=0).

    Columns:
      day_offset,timestamp,date,
      yes_daily_buy,yes_daily_sell,yes_net_tokens,yes_cumulative_position,
      no_daily_buy,no_daily_sell,no_net_tokens,no_cumulative_position,
      H_y,H_n,individual_yes_position,individual_no_position
    """
    user_tok = daily_df[daily_df["user_id"] == user_id].copy()
    if user_tok.empty:
        return pd.DataFrame()

    # Split YES / NO
    yes_df = user_tok[user_tok["token_type"] == "YES"].copy()
    no_df = user_tok[user_tok["token_type"] == "NO"].copy()

    # Get all day_offsets where user has activity
    user_offsets = sorted(set(yes_df["day_offset"]).union(no_df["day_offset"]))
    if not user_offsets:
        return pd.DataFrame()

    # First day user traded and closing day (always 0)
    first_user_day = min(user_offsets)
    closing_day = 0

    # Get market closing date (max date, day_offset=0)
    max_date = daily_df["date"].max()  # This should be the closing date (day_offset=0)
    
    # Get date/timestamp mapping for days with trades (from any user)
    market_day_info = daily_df.groupby("day_offset", as_index=False).agg(
        date=("date", "first"),
        timestamp=("timestamp", "max"),  # Use max timestamp for EOD
    )
    offset_to_info = {
        row["day_offset"]: {"date": row["date"], "timestamp": int(row["timestamp"])}
        for _, row in market_day_info.iterrows()
    }

    # Create complete range from first_user_day to closing_day (inclusive)
    all_day_offsets = list(range(first_user_day, closing_day + 1))

    rows = []
    for day_offset in all_day_offsets:
        # Compute date from day_offset: max_date + day_offset days
        d = (pd.to_datetime(max_date) + pd.Timedelta(days=day_offset)).date()
        
        # Get timestamp: use market data if available, otherwise compute from date (end of day UTC)
        if day_offset in offset_to_info:
            ts = offset_to_info[day_offset]["timestamp"]
        else:
            # Use end of day timestamp (23:59:59 UTC) for days without trades
            ts = int(pd.Timestamp(d).replace(hour=23, minute=59, second=59).timestamp())

        # Check if user has trades on this day
        yes_row = yes_df[yes_df["day_offset"] == day_offset]
        no_row = no_df[no_df["day_offset"] == day_offset]

        # Daily fields: use actual data if exists, otherwise 0
        yes_daily_buy = float(yes_row.iloc[0]["daily_buy"]) if not yes_row.empty else 0.0
        yes_daily_sell = float(yes_row.iloc[0]["daily_sell"]) if not yes_row.empty else 0.0
        yes_net = float(yes_row.iloc[0]["net_tokens"]) if not yes_row.empty else 0.0

        no_daily_buy = float(no_row.iloc[0]["daily_buy"]) if not no_row.empty else 0.0
        no_daily_sell = float(no_row.iloc[0]["daily_sell"]) if not no_row.empty else 0.0
        no_net = float(no_row.iloc[0]["net_tokens"]) if not no_row.empty else 0.0

        rows.append(
            {
                "day_offset": int(day_offset),
                "timestamp": ts,
                "date": d,
                "yes_daily_buy": yes_daily_buy,
                "yes_daily_sell": yes_daily_sell,
                "yes_net_tokens": yes_net,
                "no_daily_buy": no_daily_buy,
                "no_daily_sell": no_daily_sell,
                "no_net_tokens": no_net,
            }
        )

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows).sort_values("day_offset").reset_index(drop=True)

    # Per-market cumulative positions for this user (carried forward)
    out["yes_cumulative_position"] = out["yes_net_tokens"].cumsum()
    out["no_cumulative_position"] = out["no_net_tokens"].cumsum()

    # H_y and H_n are just per-market cumulative positions
    out["H_y"] = out["yes_cumulative_position"]
    out["H_n"] = out["no_cumulative_position"]

    # Individual yes / no positions per your formulas
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

    # Final column order
    out = out[
        [
            "day_offset",
            "timestamp",
            "date",
            "yes_daily_buy",
            "yes_daily_sell",
            "yes_net_tokens",
            "yes_cumulative_position",
            "no_daily_buy",
            "no_daily_sell",
            "no_net_tokens",
            "no_cumulative_position",
            "H_y",
            "H_n",
            "individual_yes_position",
            "individual_no_position",
        ]
    ]

    return out


# ---------- Main orchestration ----------

def process_market(event_id: str, market_slug: str) -> None:
    print(f"Processing event={event_id}, market={market_slug}...")
    try:
        trades_df = load_market_trades(event_id, market_slug)
        if trades_df.empty:
            print("  No trades found, skipping.")
            return

        daily_df = build_daily_user_token_series(trades_df)

        # Attach event/market metadata
        daily_df["event_id"] = event_id
        daily_df["market_slug"] = market_slug

        # Load prices (if available); if not, derive from trades
        prices_df = load_daily_closing_prices(event_id, market_slug)
        if prices_df is None:
            prices_df = derive_daily_prices_from_trades(trades_df)

        # For each user in this market, build and save per-user CSV
        user_ids = daily_df["user_id"].unique()
        print(f"  Found {len(user_ids)} user(s) in this market.")

        for user_id in user_ids:
            user_out = build_per_user_market_df(event_id, market_slug, daily_df, prices_df, user_id)
            if user_out.empty:
                continue

            # segment_output/<event_id>/<market_slug>/user_<user_id>.csv
            user_dir = OUTPUT_BASE / event_id / market_slug
            user_dir.mkdir(parents=True, exist_ok=True)
            out_path = user_dir / f"user_{user_id}.csv"

            user_out.to_csv(out_path, index=False)
    except Exception as e:
        print(f"  ERROR processing {event_id}/{market_slug}: {e}")


def main():
    print("Building per-market, per-user segment output from raw trades...\n")

    if not RAW_BASE.exists():
        print(f"Raw base directory not found: {RAW_BASE}")
        return

    # Iterate over events
    for event_dir in sorted(RAW_BASE.iterdir()):
        if not event_dir.is_dir() or event_dir.name.startswith("."):
            continue
        event_id = event_dir.name
        trades_dir = event_dir / "trades"
        if not trades_dir.exists():
            continue

        trade_files = sorted(trades_dir.glob("*_trades.csv"))
        if not trade_files:
            continue

        print(f"\nEvent: {event_id} ({len(trade_files)} market file(s))")

        for trade_file in trade_files:
            market_slug = trade_file.stem.replace("_trades", "")
            process_market(event_id, market_slug)

    print("\nDone. Output written under:", OUTPUT_BASE)


if __name__ == "__main__":
    main()