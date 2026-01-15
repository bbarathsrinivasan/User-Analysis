#!/usr/bin/env python3
"""
Analyze trade dates for markets to understand date distribution.

Fetches first date, last date, total trades, and date distribution for each market.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

RAW_BASE = PARENT_DIR / "data"
TARGET_EVENT = "nevada-us-senate-election-winner"

# Setup logging
def log(message: str, level: str = "INFO"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def analyze_market_trades(event_id: str, market_slug: str) -> dict:
    """Analyze trade dates for a single market."""
    trades_path = RAW_BASE / event_id / "trades" / f"{market_slug}_trades.csv"
    
    if not trades_path.exists():
        return None
    
    log(f"Analyzing: {market_slug}")
    
    # Load trades
    df = pd.read_csv(trades_path, low_memory=False)
    total_trades = len(df)
    
    # Parse timestamps
    df["unix_timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["unix_timestamp"])
    df["unix_timestamp"] = df["unix_timestamp"].astype(int)
    
    # Convert to UTC date
    df["datetime"] = pd.to_datetime(df["unix_timestamp"], unit="s", utc=True)
    df["date"] = df["datetime"].dt.date
    
    # Calculate statistics
    first_date = df["date"].min()
    last_date = df["date"].max()
    date_range_days = (pd.to_datetime(last_date) - pd.to_datetime(first_date)).days + 1
    
    # Count trades per date
    trades_per_date = df.groupby("date").size().sort_index()
    unique_dates = len(trades_per_date)
    
    # Calculate day_offset (relative to last date)
    max_date = df["date"].max()
    df["day_offset"] = (pd.to_datetime(df["date"]) - pd.to_datetime(max_date)).dt.days
    
    # Count trades per day_offset
    trades_per_offset = df.groupby("day_offset").size().sort_index()
    
    # Get top 10 days by trade count
    top_days = trades_per_date.nlargest(10)
    
    result = {
        "market_slug": market_slug,
        "total_trades": total_trades,
        "first_date": first_date,
        "last_date": last_date,
        "date_range_days": date_range_days,
        "unique_dates": unique_dates,
        "trades_per_date": trades_per_date,
        "trades_per_offset": trades_per_offset,
        "top_10_days": top_days,
    }
    
    return result


def print_market_summary(result: dict):
    """Print summary for a market."""
    print("\n" + "=" * 80)
    print(f"Market: {result['market_slug']}")
    print("=" * 80)
    print(f"Total Trades: {result['total_trades']:,}")
    print(f"First Trade Date: {result['first_date']}")
    print(f"Last Trade Date: {result['last_date']}")
    print(f"Date Range: {result['date_range_days']} calendar days")
    print(f"Unique Trading Days: {result['unique_dates']}")
    print(f"\nDay Offset Range: {result['trades_per_offset'].index.min()} to {result['trades_per_offset'].index.max()}")
    print(f"Unique Day Offsets: {len(result['trades_per_offset'])}")
    
    print("\nTop 10 Days by Trade Count:")
    print("-" * 80)
    for date, count in result['top_10_days'].items():
        day_offset = (pd.to_datetime(date) - pd.to_datetime(result['last_date'])).days
        percentage = (count / result['total_trades']) * 100
        print(f"  {date} (day_offset={day_offset:4d}): {count:>12,} trades ({percentage:>6.2f}%)")
    
    print("\nAll Days with Trades (sorted by date):")
    print("-" * 80)
    for date, count in result['trades_per_date'].items():
        day_offset = (pd.to_datetime(date) - pd.to_datetime(result['last_date'])).days
        percentage = (count / result['total_trades']) * 100
        print(f"  {date} (day_offset={day_offset:4d}): {count:>12,} trades ({percentage:>6.2f}%)")
    
    print("\nDay Offset Distribution:")
    print("-" * 80)
    for day_offset, count in result['trades_per_offset'].items():
        percentage = (count / result['total_trades']) * 100
        print(f"  day_offset={day_offset:4d}: {count:>12,} trades ({percentage:>6.2f}%)")


def check_aggregated_output(event_id: str, market_slug: str) -> dict:
    """Check what day_offsets are in the aggregated output."""
    output_path = Path(__file__).parent / "output" / "segment_aggregation" / event_id / market_slug / "all_segments.csv"
    
    if not output_path.exists():
        return None
    
    df = pd.read_csv(output_path, low_memory=False)
    
    # Count days with valid odds (non-NaN)
    days_with_valid_odds = df[df["odds"].notna()].copy()
    days_with_zero_positions = df[(df["agg_yes"] == 0) & (df["agg_no"] == 0)].copy()
    days_with_activity = df[((df["agg_yes"] > 0) | (df["agg_no"] > 0))].copy()
    
    return {
        "day_offsets_in_output": sorted(df["day_offset"].unique()),
        "total_day_offsets": len(df["day_offset"].unique()),
        "days_with_valid_odds": len(days_with_valid_odds),
        "days_with_zero_positions": len(days_with_zero_positions),
        "days_with_activity": len(days_with_activity),
        "output_df": df,
        "days_with_valid_odds_df": days_with_valid_odds
    }


def main():
    """Main function to analyze all markets."""
    log("=" * 80)
    log("Analyzing Trade Dates for Nevada Event")
    log("=" * 80)
    
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
    
    log(f"\nFound {len(trade_files)} market(s) to analyze")
    log("-" * 80)
    
    results = []
    for trade_file in trade_files:
        market_slug = trade_file.stem.replace("_trades", "")
        result = analyze_market_trades(TARGET_EVENT, market_slug)
        if result:
            results.append(result)
            print_market_summary(result)
            
            # Check aggregated output
            agg_info = check_aggregated_output(TARGET_EVENT, market_slug)
            if agg_info:
                print("\n" + "-" * 80)
                print("AGGREGATED OUTPUT ANALYSIS:")
                print("-" * 80)
                print(f"Total day offsets in output: {agg_info['total_day_offsets']}")
                print(f"Day offsets with valid odds (non-NaN): {agg_info['days_with_valid_odds']}")
                print(f"Day offsets with zero positions (NaN odds): {agg_info['days_with_zero_positions']}")
                print(f"Day offsets with trading activity: {agg_info['days_with_activity']}")
                print(f"\nDay offsets in raw trades: {result['unique_dates']}")
                
                if agg_info['days_with_valid_odds'] < result['unique_dates']:
                    print(f"\n⚠️  WARNING: Only {agg_info['days_with_valid_odds']} days have valid odds out of {result['unique_dates']} trading days!")
                    print("This means many days had trades but resulted in zero aggregated positions.")
                    print("Possible reasons:")
                    print("  - Trades were from users without segment mappings")
                    print("  - Trades resulted in zero net positions (buy/sell balanced)")
                    print("  - Individual positions calculated to zero")
                    print("\nDays with valid odds (will appear in graph):")
                    valid_days = agg_info['days_with_valid_odds_df'].sort_values('day_offset')
                    for _, row in valid_days.iterrows():
                        day_offset = int(row['day_offset'])
                        print(f"  day_offset={day_offset:4d}: odds={row['odds']:.4f} (agg_yes={row['agg_yes']:.1f}, agg_no={row['agg_no']:.1f})")
                else:
                    print("✓ All trading days have valid odds in the aggregated output")
    
    # Overall summary
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    total_trades_all = sum(r['total_trades'] for r in results)
    print(f"Total Markets Analyzed: {len(results)}")
    print(f"Total Trades Across All Markets: {total_trades_all:,}")
    
    if results:
        earliest_date = min(r['first_date'] for r in results)
        latest_date = max(r['last_date'] for r in results)
        print(f"\nEarliest Trade Date (across all markets): {earliest_date}")
        print(f"Latest Trade Date (across all markets): {latest_date}")
        overall_range = (pd.to_datetime(latest_date) - pd.to_datetime(earliest_date)).days + 1
        print(f"Overall Date Range: {overall_range} calendar days")
    
    print("\n" + "=" * 80)
    log("Analysis completed")


if __name__ == "__main__":
    main()
