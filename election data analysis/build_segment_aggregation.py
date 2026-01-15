#!/usr/bin/env python3
"""
Build segment-based aggregation files and comparison graphs for each market.

For wisconsin-us-senate-election-winner event only.

Outputs to: election data analysis/output/segment_aggregation/
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Add parent directory to path
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

SEGMENT_OUTPUT_BASE = Path(__file__).parent / "output" / "segment_positions"
RAW_BASE = Path(__file__).parent / "data"
SEGMENT_BASE = Path(__file__).parent / "output" / "segment_aggregation"
ANALYSIS_CSV = PARENT_DIR / "all_users_analysis.csv"
DONATIONS_BASE = Path(__file__).parent / "output" / "donations"
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


def load_segment_mapping() -> Dict[str, str]:
    """Load user_id -> segment mapping from all_users_analysis.csv."""
    log(f"Loading segment mapping from: {ANALYSIS_CSV.name}")
    
    if not ANALYSIS_CSV.exists():
        log(f"Segment mapping file not found: {ANALYSIS_CSV}", "ERROR")
        return {}
    
    try:
        df = pd.read_csv(ANALYSIS_CSV, low_memory=False)
    except Exception as e:
        log(f"Error reading segment mapping file: {e}", "ERROR")
        return {}
    
    segment_map = {}
    for _, row in df.iterrows():
        user_id = str(row["user_id"]).strip()
        segment = str(row["user_segment"]).strip()
        if segment and segment != "nan":
            segment_map[user_id] = segment
    
    log(f"Loaded {len(segment_map)} user segments", "SUCCESS")
    
    # Count segments
    segment_counts = {}
    for segment in segment_map.values():
        segment_counts[segment] = segment_counts.get(segment, 0) + 1
    
    for segment, count in sorted(segment_counts.items()):
        log(f"  {segment}: {count} users", "INFO")
    
    return segment_map


def get_market_closing_date(event_id: str, market_slug: str) -> Optional[pd.Timestamp]:
    """Get the closing date (day_offset=0) for a market by finding max date in user files."""
    market_dir = SEGMENT_OUTPUT_BASE / event_id / market_slug
    if not market_dir.exists():
        return None
    
    user_files = list(market_dir.glob("user_*.csv"))
    if not user_files:
        return None
    
    try:
        df = pd.read_csv(user_files[0], low_memory=False)
        closing_row = df[df["day_offset"] == 0]
        if not closing_row.empty:
            closing_date = pd.to_datetime(closing_row.iloc[0]["date"])
            return closing_date
    except Exception:
        pass
    
    return None


def get_market_date_range(event_id: str, market_slug: str) -> Tuple[int, int]:
    """
    Get the first and last day_offset from raw trade data.
    Returns (first_day_offset, last_day_offset) where last_day_offset is always 0.
    """
    trades_path = RAW_BASE / event_id / "trades" / f"{market_slug}_trades.csv"
    if not trades_path.exists():
        return None, None
    
    try:
        df = pd.read_csv(trades_path, low_memory=False)
        df["unix_timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["unix_timestamp"])
        df["unix_timestamp"] = df["unix_timestamp"].astype(int)
        
        # Convert to UTC date
        df["datetime"] = pd.to_datetime(df["unix_timestamp"], unit="s", utc=True)
        df["date"] = df["datetime"].dt.date
        
        # Calculate day_offset (relative to last date)
        max_date = df["date"].max()
        df["day_offset"] = (pd.to_datetime(df["date"]) - pd.to_datetime(max_date)).dt.days
        
        first_day_offset = int(df["day_offset"].min())
        last_day_offset = 0  # Always 0 (closing day)
        
        return first_day_offset, last_day_offset
    except Exception as e:
        log(f"  Error getting date range: {e}", "WARNING")
        return None, None


def load_price_odds(event_id: str, market_slug: str) -> Optional[pd.DataFrame]:
    """Load YES closing prices from price file and convert to day_offset."""
    prices_path = RAW_BASE / event_id / "prices" / f"{market_slug}_closing_prices.csv"
    if not prices_path.exists():
        prices_path = RAW_BASE / event_id / "prices" / f"{market_slug}_price.csv"
        if not prices_path.exists():
            return None
    
    try:
        df = pd.read_csv(prices_path, low_memory=False)
        if df.empty:
            return None
        
        if "date" in df.columns and "token_type" in df.columns:
            price_col = "closing_price" if "closing_price" in df.columns else "price"
            if price_col not in df.columns:
                return None
                
            yes_prices = df[df["token_type"] == "YES"].copy()
            if yes_prices.empty:
                return None
            
            yes_prices["date"] = pd.to_datetime(yes_prices["date"])
            
            closing_date = get_market_closing_date(event_id, market_slug)
            if closing_date is None:
                return None
            
            if not isinstance(closing_date, pd.Timestamp):
                closing_date = pd.to_datetime(closing_date)
            
            yes_prices["day_offset"] = (yes_prices["date"] - closing_date).dt.days
            yes_prices = yes_prices[yes_prices["day_offset"] <= 0].copy()
            
            if yes_prices.empty:
                return None
            
            yes_prices = yes_prices.sort_values("date")
            daily_closing = yes_prices.groupby("day_offset").last().reset_index()
            
            result = daily_closing[["day_offset", price_col]].copy()
            result.rename(columns={price_col: "price_odds"}, inplace=True)
            result = result.sort_values("day_offset").reset_index(drop=True)
            
            return result
        elif "timestamp" in df.columns and "token_id" in df.columns and "price" in df.columns:
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
            
            yes_prices = df[df["token_type"] == "YES"].copy()
            if yes_prices.empty:
                return None
            
            yes_prices['timestamp'] = pd.to_numeric(yes_prices['timestamp'], errors='coerce')
            yes_prices = yes_prices.dropna(subset=['timestamp'])
            yes_prices['datetime'] = pd.to_datetime(yes_prices['timestamp'], unit='s', utc=True)
            yes_prices['date'] = yes_prices['datetime'].dt.date
            yes_prices['date_dt'] = pd.to_datetime(yes_prices['date'])
            
            closing_date = get_market_closing_date(event_id, market_slug)
            if closing_date is None:
                return None
            
            if not isinstance(closing_date, pd.Timestamp):
                closing_date = pd.to_datetime(closing_date)
            
            yes_prices["day_offset"] = (yes_prices["date_dt"] - closing_date).dt.days
            yes_prices = yes_prices[yes_prices["day_offset"] <= 0].copy()
            
            if yes_prices.empty:
                return None
            
            yes_prices = yes_prices.sort_values('timestamp')
            daily_closing_by_date = yes_prices.groupby("date").last().reset_index()
            
            daily_closing_by_date['date_dt'] = pd.to_datetime(daily_closing_by_date['date'])
            daily_closing_by_date["day_offset"] = (daily_closing_by_date["date_dt"] - closing_date).dt.days
            daily_closing_by_date = daily_closing_by_date[daily_closing_by_date["day_offset"] <= 0].copy()
            
            if daily_closing_by_date.empty:
                return None
            
            daily_closing = daily_closing_by_date.sort_values('date_dt').groupby("day_offset").last().reset_index()
            
            result = daily_closing[["day_offset", "price"]].copy()
            result.rename(columns={"price": "price_odds"}, inplace=True)
            result = result.sort_values("day_offset").reset_index(drop=True)
            
            return result
        else:
            return None
    except Exception as e:
        log(f"Error loading prices: {e}", "WARNING")
        return None


def aggregate_market_segments(
    event_id: str, market_slug: str, segment_map: Dict[str, str]
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Aggregate individual positions by segment for a market."""
    market_dir = SEGMENT_OUTPUT_BASE / event_id / market_slug
    if not market_dir.exists():
        return None, None, None, None
    
    user_files = list(market_dir.glob("user_*.csv"))
    if not user_files:
        return None, None, None, None
    
    log(f"  Aggregating {len(user_files)} user files...")
    
    all_data = []
    users_with_segment = 0
    users_without_segment = 0
    
    for user_file in user_files:
        user_id = user_file.stem.replace("user_", "")
        segment = segment_map.get(user_id)
        
        if segment is None:
            users_without_segment += 1
            continue
        
        users_with_segment += 1
        try:
            df = pd.read_csv(user_file, low_memory=False)
            if df.empty:
                continue
            
            df["user_id"] = user_id
            df["segment"] = segment
            all_data.append(df)
        except Exception as e:
            log(f"  Warning: Error reading {user_file.name}: {e}", "WARNING")
            continue
    
    if users_without_segment > 0:
        log(f"  {users_without_segment} users without segment mapping (skipped)", "INFO")
    
    if not all_data:
        return None, None, None, None
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Get the full date range from raw trade data
    first_day_offset, last_day_offset = get_market_date_range(event_id, market_slug)
    if first_day_offset is None or last_day_offset is None:
        # Fallback to using only days with data
        all_day_offsets = sorted(combined_df["day_offset"].unique())
        first_day_offset = min(all_day_offsets) if all_day_offsets else 0
        last_day_offset = max(all_day_offsets) if all_day_offsets else 0
        log(f"  Warning: Could not get date range from raw data, using data range: {first_day_offset} to {last_day_offset}", "WARNING")
    else:
        log(f"  Date range from raw trades: day_offset {first_day_offset} to {last_day_offset}")
    
    # Create full range of day offsets
    full_day_offsets = list(range(first_day_offset, last_day_offset + 1))
    log(f"  Processing {len(full_day_offsets)} day offsets (filling all days from first to last trade)...")
    
    results = {
        "all": [],
        "Small": [],
        "Medium": [],
        "Large": []
    }
    
    # Track previous values for carry-forward
    prev_values = {
        "all": {"agg_yes": 0.0, "agg_no": 0.0},
        "Small": {"agg_yes": 0.0, "agg_no": 0.0},
        "Medium": {"agg_yes": 0.0, "agg_no": 0.0},
        "Large": {"agg_yes": 0.0, "agg_no": 0.0}
    }
    
    for day_offset in full_day_offsets:
        day_data = combined_df[combined_df["day_offset"] == day_offset].copy()
        
        for segment_key in ["all", "Small", "Medium", "Large"]:
            if segment_key == "all":
                segment_data = day_data.copy()
            else:
                segment_data = day_data[day_data["segment"] == segment_key].copy()
            
            if not segment_data.empty:
                # We have data for this day
                yes_users = segment_data[segment_data["yes_cumulative_position"] != 0]
                agg_yes = yes_users["individual_yes_position"].sum()
                
                no_users = segment_data[segment_data["no_cumulative_position"] != 0]
                agg_no = no_users["individual_no_position"].sum()
                
                # Update previous values
                prev_values[segment_key]["agg_yes"] = float(agg_yes)
                prev_values[segment_key]["agg_no"] = float(agg_no)
            else:
                # No data for this day - carry forward from previous day
                agg_yes = prev_values[segment_key]["agg_yes"]
                agg_no = prev_values[segment_key]["agg_no"]
            
            total = agg_yes + agg_no
            if total > 0:
                odds = agg_yes / total
            else:
                odds = np.nan
            
            results[segment_key].append({
                "day_offset": int(day_offset),
                "agg_yes": float(agg_yes),
                "agg_no": float(agg_no),
                "odds": float(odds) if not np.isnan(odds) else np.nan
            })
    
    all_segments_df = pd.DataFrame(results["all"])
    small_segment_df = pd.DataFrame(results["Small"])
    medium_segment_df = pd.DataFrame(results["Medium"])
    large_segment_df = pd.DataFrame(results["Large"])
    
    return all_segments_df, small_segment_df, medium_segment_df, large_segment_df


def load_donation_data(market_slug: str) -> Optional[pd.DataFrame]:
    """
    Load donation data based on market slug.
    
    Returns DataFrame with columns: day_offset, normalized_donation
    or None if not found/not applicable
    """
    # Determine which candidate based on market slug
    if "democrat" in market_slug.lower():
        donation_file = DONATIONS_BASE / "baldwin_donations.csv"
        candidate_name = "Baldwin"
    elif "republican" in market_slug.lower():
        donation_file = DONATIONS_BASE / "hovde_donations.csv"
        candidate_name = "Hovde"
    else:
        # Not a candidate-specific market, skip donations
        return None
    
    if not donation_file.exists():
        log(f"  Donation file not found: {donation_file.name}", "WARNING")
        return None
    
    try:
        df = pd.read_csv(donation_file, low_memory=False)
        if df.empty:
            return None
        
        # Select only day_offset and normalized_donation columns
        result = df[['day_offset', 'normalized_donation']].copy()
        result = result.sort_values('day_offset').reset_index(drop=True)
        
        log(f"  Loaded {len(result)} donation data points for {candidate_name}", "INFO")
        return result
    except Exception as e:
        log(f"  Error loading donation data: {e}", "WARNING")
        return None


def plot_odds_comparison(
    event_id: str,
    market_slug: str,
    price_df: Optional[pd.DataFrame],
    all_segments_df: pd.DataFrame,
    small_segment_df: pd.DataFrame,
    medium_segment_df: pd.DataFrame,
    large_segment_df: pd.DataFrame,
    donation_df: Optional[pd.DataFrame] = None,
) -> None:
    """Create 3 comparison graphs: original (no donation), donation-only, and combined."""
    output_dir = SEGMENT_BASE / event_id / market_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    
    graphs_created = []
    
    # Graph 1: Original (without donation)
    fig1, ax1 = plt.subplots(figsize=(12, 8))
    lines_plotted_1 = 0
    
    if price_df is not None and not price_df.empty:
        ax1.plot(
            price_df["day_offset"],
            price_df["price_odds"],
            color="blue",
            linewidth=2,
            label="Price-based Market Odds",
            marker="o",
            markersize=3
        )
        lines_plotted_1 += 1
    
    if all_segments_df is not None and not all_segments_df.empty:
        # Forward-fill NaN odds for continuous plotting
        plot_df = all_segments_df.copy()
        plot_df["odds"] = plot_df["odds"].ffill()
        ax1.plot(
            plot_df["day_offset"],
            plot_df["odds"],
            color="green",
            linewidth=2,
            label="All Segments (Investment-based)",
            marker="s",
            markersize=3
        )
        lines_plotted_1 += 1
    
    if small_segment_df is not None and not small_segment_df.empty:
        plot_df = small_segment_df.copy()
        plot_df["odds"] = plot_df["odds"].ffill()
        ax1.plot(
            plot_df["day_offset"],
            plot_df["odds"],
            color="orange",
            linewidth=2,
            label="Small Segment (Investment-based)",
            marker="^",
            markersize=3
        )
        lines_plotted_1 += 1
    
    if medium_segment_df is not None and not medium_segment_df.empty:
        plot_df = medium_segment_df.copy()
        plot_df["odds"] = plot_df["odds"].ffill()
        ax1.plot(
            plot_df["day_offset"],
            plot_df["odds"],
            color="red",
            linewidth=2,
            label="Medium Segment (Investment-based)",
            marker="v",
            markersize=3
        )
        lines_plotted_1 += 1
    
    if large_segment_df is not None and not large_segment_df.empty:
        plot_df = large_segment_df.copy()
        plot_df["odds"] = plot_df["odds"].ffill()
        ax1.plot(
            plot_df["day_offset"],
            plot_df["odds"],
            color="purple",
            linewidth=2,
            label="Large Segment (Investment-based)",
            marker="d",
            markersize=3
        )
        lines_plotted_1 += 1
    
    ax1.set_xlabel("Day Offset (0 = Closing Day)", fontsize=12)
    ax1.set_ylabel("Odds (0 to 1)", fontsize=12)
    ax1.set_title(f"Odds Comparison (Original): {market_slug}", fontsize=14, fontweight="bold")
    ax1.set_ylim(0, 1)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="best", fontsize=10)
    
    output_path_1 = output_dir / "odds_comparison_original.png"
    plt.tight_layout()
    plt.savefig(output_path_1, dpi=300, bbox_inches="tight")
    plt.close()
    graphs_created.append(f"odds_comparison_original.png ({lines_plotted_1} lines)")
    
    # Graph 2: Donation-only
    if donation_df is not None and not donation_df.empty:
        fig2, ax2 = plt.subplots(figsize=(12, 8))
        
        ax2.plot(
            donation_df["day_offset"],
            donation_df["normalized_donation"],
            color="brown",
            linewidth=2,
            label="Election Donations (Normalized)",
            marker="x",
            markersize=4
        )
        
        ax2.set_xlabel("Day Offset (0 = Closing Day)", fontsize=12)
        ax2.set_ylabel("Normalized Donation (Daily/Total)", fontsize=12)
        ax2.set_title(f"Election Donations: {market_slug}", fontsize=14, fontweight="bold")
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc="best", fontsize=10)
        
        output_path_2 = output_dir / "odds_comparison_donations.png"
        plt.tight_layout()
        plt.savefig(output_path_2, dpi=300, bbox_inches="tight")
        plt.close()
        graphs_created.append(f"odds_comparison_donations.png (1 line)")
    
    # Graph 3: Combined (with donation)
    fig3, ax3 = plt.subplots(figsize=(12, 8))
    lines_plotted_3 = 0
    
    if price_df is not None and not price_df.empty:
        ax3.plot(
            price_df["day_offset"],
            price_df["price_odds"],
            color="blue",
            linewidth=2,
            label="Price-based Market Odds",
            marker="o",
            markersize=3
        )
        lines_plotted_3 += 1
    
    if all_segments_df is not None and not all_segments_df.empty:
        plot_df = all_segments_df.copy()
        plot_df["odds"] = plot_df["odds"].ffill()
        ax3.plot(
            plot_df["day_offset"],
            plot_df["odds"],
            color="green",
            linewidth=2,
            label="All Segments (Investment-based)",
            marker="s",
            markersize=3
        )
        lines_plotted_3 += 1
    
    if small_segment_df is not None and not small_segment_df.empty:
        plot_df = small_segment_df.copy()
        plot_df["odds"] = plot_df["odds"].ffill()
        ax3.plot(
            plot_df["day_offset"],
            plot_df["odds"],
            color="orange",
            linewidth=2,
            label="Small Segment (Investment-based)",
            marker="^",
            markersize=3
        )
        lines_plotted_3 += 1
    
    if medium_segment_df is not None and not medium_segment_df.empty:
        plot_df = medium_segment_df.copy()
        plot_df["odds"] = plot_df["odds"].ffill()
        ax3.plot(
            plot_df["day_offset"],
            plot_df["odds"],
            color="red",
            linewidth=2,
            label="Medium Segment (Investment-based)",
            marker="v",
            markersize=3
        )
        lines_plotted_3 += 1
    
    if large_segment_df is not None and not large_segment_df.empty:
        plot_df = large_segment_df.copy()
        plot_df["odds"] = plot_df["odds"].ffill()
        ax3.plot(
            plot_df["day_offset"],
            plot_df["odds"],
            color="purple",
            linewidth=2,
            label="Large Segment (Investment-based)",
            marker="d",
            markersize=3
        )
        lines_plotted_3 += 1
    
    # Plot donation line
    if donation_df is not None and not donation_df.empty:
        ax3.plot(
            donation_df["day_offset"],
            donation_df["normalized_donation"],
            color="brown",
            linewidth=2,
            label="Election Donations (Normalized)",
            marker="x",
            markersize=4
        )
        lines_plotted_3 += 1
    
    ax3.set_xlabel("Day Offset (0 = Closing Day)", fontsize=12)
    ax3.set_ylabel("Odds (0 to 1)", fontsize=12)
    ax3.set_title(f"Odds Comparison (Combined): {market_slug}", fontsize=14, fontweight="bold")
    ax3.set_ylim(0, 1)
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc="best", fontsize=10)
    
    output_path_3 = output_dir / "odds_comparison.png"
    plt.tight_layout()
    plt.savefig(output_path_3, dpi=300, bbox_inches="tight")
    plt.close()
    graphs_created.append(f"odds_comparison.png ({lines_plotted_3} lines)")
    
    log(f"  Created {len(graphs_created)} graphs: {', '.join(graphs_created)}", "SUCCESS")


def process_market(event_id: str, market_slug: str, segment_map: Dict[str, str], market_num: int, total_markets: int) -> None:
    """Process a single market: create CSVs and graph."""
    log(f"[Market {market_num}/{total_markets}] Processing: {market_slug}")
    start_time = datetime.now()
    
    all_segments_df, small_segment_df, medium_segment_df, large_segment_df = aggregate_market_segments(
        event_id, market_slug, segment_map
    )
    
    if all_segments_df is None or all_segments_df.empty:
        log("  No data found, skipping.", "WARNING")
        return
    
    output_dir = SEGMENT_BASE / event_id / market_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_segments_df.to_csv(output_dir / "all_segments.csv", index=False)
    small_segment_df.to_csv(output_dir / "small_segment.csv", index=False)
    medium_segment_df.to_csv(output_dir / "medium_segment.csv", index=False)
    large_segment_df.to_csv(output_dir / "large_segment.csv", index=False)
    
    log(f"  Created 4 CSV files", "SUCCESS")
    
    price_df = load_price_odds(event_id, market_slug)
    if price_df is not None and not price_df.empty:
        log(f"  Loaded {len(price_df)} price data points", "INFO")
    else:
        log("  No price data available (graph will show investment-based odds only)", "WARNING")
    
    # Load donation data
    donation_df = load_donation_data(market_slug)
    
    plot_odds_comparison(
        event_id, market_slug,
        price_df,
        all_segments_df, small_segment_df, medium_segment_df, large_segment_df,
        donation_df
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    log(f"  ✓ Completed in {elapsed:.1f}s", "SUCCESS")


def main():
    """Main function: process all markets."""
    log("=" * 80)
    log("Building segment aggregation files and comparison graphs")
    log(f"Target Event: {TARGET_EVENT}")
    log("=" * 80)
    
    segment_map = load_segment_mapping()
    
    if not segment_map:
        log("Error: No segment mappings found. Exiting.", "ERROR")
        return
    
    if not SEGMENT_OUTPUT_BASE.exists():
        log(f"Error: Segment output directory not found: {SEGMENT_OUTPUT_BASE}", "ERROR")
        log("Please run build_segment_positions.py first", "ERROR")
        return
    
    event_dir = SEGMENT_OUTPUT_BASE / TARGET_EVENT
    if not event_dir.exists():
        log(f"Error: Event directory not found: {event_dir}", "ERROR")
        return
    
    market_dirs = [d for d in sorted(event_dir.iterdir()) if d.is_dir()]
    if not market_dirs:
        log(f"No market directories found in {event_dir}", "ERROR")
        return
    
    total_markets = len(market_dirs)
    log(f"\nFound {total_markets} market(s) to process")
    log(f"Output directory: {SEGMENT_BASE}")
    log("-" * 80)
    
    overall_start = datetime.now()
    markets_processed = 0
    
    for market_idx, market_dir in enumerate(market_dirs, 1):
        market_slug = market_dir.name
        process_market(TARGET_EVENT, market_slug, segment_map, market_idx, total_markets)
        markets_processed += 1
        
        if market_idx < total_markets:
            log_progress(market_idx, total_markets, "market")
            log("")
    
    overall_elapsed = (datetime.now() - overall_start).total_seconds()
    log("=" * 80)
    log(f"✓ All markets processed successfully in {overall_elapsed:.1f} seconds")
    log(f"Output written to: {SEGMENT_BASE}")
    log("=" * 80)


if __name__ == "__main__":
    main()

