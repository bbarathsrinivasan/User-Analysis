#!/usr/bin/env python3
"""
Build segment-based aggregation files and comparison graphs for each market.

For each market, creates:
- 4 CSV files: all_segments.csv, small_segment.csv, medium_segment.csv, large_segment.csv
- 1 graph: odds_comparison.png (5 lines: price-based + 4 investment-based)
"""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

SEGMENT_OUTPUT_BASE = Path("segment_output")
RAW_BASE = Path("raw")
SEGMENT_BASE = Path("segment")
ANALYSIS_CSV = Path("all_users_analysis.csv")


def load_segment_mapping() -> Dict[str, str]:
    """
    Load user_id -> segment mapping from all_users_analysis.csv.
    
    Returns:
        Dictionary mapping user_id (str) to segment ("Small", "Medium", or "Large")
    """
    print("Loading segment mapping from all_users_analysis.csv...")
    df = pd.read_csv(ANALYSIS_CSV, low_memory=False)
    
    # Create mapping: user_id -> user_segment
    segment_map = {}
    for _, row in df.iterrows():
        user_id = str(row["user_id"]).strip()
        segment = str(row["user_segment"]).strip()
        if segment and segment != "nan":
            segment_map[user_id] = segment
    
    print(f"  Loaded {len(segment_map)} user segments")
    return segment_map


def get_market_closing_date(event_id: str, market_slug: str) -> Optional[pd.Timestamp]:
    """
    Get the closing date (day_offset=0) for a market by finding max date in user files.
    
    Returns:
        pd.Timestamp of the closing date, or None if no data found
    """
    market_dir = SEGMENT_OUTPUT_BASE / event_id / market_slug
    if not market_dir.exists():
        return None
    
    user_files = list(market_dir.glob("user_*.csv"))
    if not user_files:
        return None
    
    # Read first user file to get the date for day_offset=0
    try:
        df = pd.read_csv(user_files[0], low_memory=False)
        closing_row = df[df["day_offset"] == 0]
        if not closing_row.empty:
            closing_date = pd.to_datetime(closing_row.iloc[0]["date"])
            return closing_date
    except Exception:
        pass
    
    return None


def load_price_odds(event_id: str, market_slug: str) -> Optional[pd.DataFrame]:
    """
    Load YES closing prices from price file and convert to day_offset.
    
    Returns:
        DataFrame with columns: day_offset, price_odds
        or None if price file not found
    """
    prices_path = RAW_BASE / event_id / "prices" / f"{market_slug}_closing_prices.csv"
    if not prices_path.exists():
        return None
    
    try:
        df = pd.read_csv(prices_path, low_memory=False)
        if df.empty:
            return None
        
        # Filter YES prices only
        yes_prices = df[df["token_type"] == "YES"].copy()
        if yes_prices.empty:
            return None
        
        # Convert date to datetime
        yes_prices["date"] = pd.to_datetime(yes_prices["date"])
        
        # Get market closing date to compute day_offset
        closing_date = get_market_closing_date(event_id, market_slug)
        if closing_date is None:
            return None
        
        # Compute day_offset: (date - closing_date).days
        yes_prices["day_offset"] = (yes_prices["date"] - closing_date).dt.days
        
        # Filter out any prices with day_offset > 0 (after closing date)
        # Only keep prices from closing date or earlier (day_offset <= 0)
        yes_prices = yes_prices[yes_prices["day_offset"] <= 0].copy()
        
        if yes_prices.empty:
            return None
        
        # Select columns and rename
        result = yes_prices[["day_offset", "closing_price"]].copy()
        result.rename(columns={"closing_price": "price_odds"}, inplace=True)
        result = result.sort_values("day_offset").reset_index(drop=True)
        
        return result
    except Exception as e:
        print(f"  Error loading prices: {e}")
        return None


def aggregate_market_segments(
    event_id: str, market_slug: str, segment_map: Dict[str, str]
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Aggregate individual positions by segment for a market.
    
    Returns:
        Tuple of 4 DataFrames: (all_segments, small_segment, medium_segment, large_segment)
        Each DataFrame has columns: day_offset, agg_yes, agg_no, odds
    """
    market_dir = SEGMENT_OUTPUT_BASE / event_id / market_slug
    if not market_dir.exists():
        return None, None, None, None
    
    user_files = list(market_dir.glob("user_*.csv"))
    if not user_files:
        return None, None, None, None
    
    # Collect all user data
    all_data = []
    for user_file in user_files:
        # Extract user_id from filename: user_0x...csv -> 0x...
        user_id = user_file.stem.replace("user_", "")
        
        # Get segment for this user
        segment = segment_map.get(user_id)
        if segment is None:
            continue  # Skip users without segment mapping
        
        try:
            df = pd.read_csv(user_file, low_memory=False)
            if df.empty:
                continue
            
            # Add user_id and segment columns
            df["user_id"] = user_id
            df["segment"] = segment
            all_data.append(df)
        except Exception as e:
            print(f"  Warning: Error reading {user_file.name}: {e}")
            continue
    
    if not all_data:
        return None, None, None, None
    
    # Combine all user data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Get all unique day_offsets
    all_day_offsets = sorted(combined_df["day_offset"].unique())
    
    # Initialize result DataFrames
    results = {
        "all": [],
        "Small": [],
        "Medium": [],
        "Large": []
    }
    
    for day_offset in all_day_offsets:
        day_data = combined_df[combined_df["day_offset"] == day_offset].copy()
        
        # Process each segment
        for segment_key in ["all", "Small", "Medium", "Large"]:
            if segment_key == "all":
                segment_data = day_data.copy()
            else:
                segment_data = day_data[day_data["segment"] == segment_key].copy()
            
            # Aggregate YES positions: sum individual_yes_position for users with yes_cumulative_position != 0
            yes_users = segment_data[segment_data["yes_cumulative_position"] != 0]
            agg_yes = yes_users["individual_yes_position"].sum()
            
            # Aggregate NO positions: sum individual_no_position for users with no_cumulative_position != 0
            no_users = segment_data[segment_data["no_cumulative_position"] != 0]
            agg_no = no_users["individual_no_position"].sum()
            
            # Calculate odds
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
    
    # Create DataFrames
    all_segments_df = pd.DataFrame(results["all"])
    small_segment_df = pd.DataFrame(results["Small"])
    medium_segment_df = pd.DataFrame(results["Medium"])
    large_segment_df = pd.DataFrame(results["Large"])
    
    return all_segments_df, small_segment_df, medium_segment_df, large_segment_df


def plot_odds_comparison(
    event_id: str,
    market_slug: str,
    price_df: Optional[pd.DataFrame],
    all_segments_df: pd.DataFrame,
    small_segment_df: pd.DataFrame,
    medium_segment_df: pd.DataFrame,
    large_segment_df: pd.DataFrame,
) -> None:
    """
    Create 5-line comparison graph: price-based odds + 4 investment-based odds.
    """
    output_dir = SEGMENT_BASE / event_id / market_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot price-based odds (blue)
    if price_df is not None and not price_df.empty:
        ax.plot(
            price_df["day_offset"],
            price_df["price_odds"],
            color="blue",
            linewidth=2,
            label="Price-based Market Odds",
            marker="o",
            markersize=3
        )
    
    # Plot investment-based odds
    if all_segments_df is not None and not all_segments_df.empty:
        ax.plot(
            all_segments_df["day_offset"],
            all_segments_df["odds"],
            color="green",
            linewidth=2,
            label="All Segments (Investment-based)",
            marker="s",
            markersize=3
        )
    
    if small_segment_df is not None and not small_segment_df.empty:
        ax.plot(
            small_segment_df["day_offset"],
            small_segment_df["odds"],
            color="orange",
            linewidth=2,
            label="Small Segment (Investment-based)",
            marker="^",
            markersize=3
        )
    
    if medium_segment_df is not None and not medium_segment_df.empty:
        ax.plot(
            medium_segment_df["day_offset"],
            medium_segment_df["odds"],
            color="red",
            linewidth=2,
            label="Medium Segment (Investment-based)",
            marker="v",
            markersize=3
        )
    
    if large_segment_df is not None and not large_segment_df.empty:
        ax.plot(
            large_segment_df["day_offset"],
            large_segment_df["odds"],
            color="purple",
            linewidth=2,
            label="Large Segment (Investment-based)",
            marker="d",
            markersize=3
        )
    
    # Formatting
    ax.set_xlabel("Day Offset (0 = Closing Day)", fontsize=12)
    ax.set_ylabel("Odds (0 to 1)", fontsize=12)
    ax.set_title(f"Odds Comparison: {market_slug}", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=10)
    
    # Save figure
    output_path = output_dir / "odds_comparison.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"  Created graph: {output_path}")


def process_market(event_id: str, market_slug: str, segment_map: Dict[str, str]) -> None:
    """Process a single market: create CSVs and graph."""
    print(f"\nProcessing market: {event_id}/{market_slug}")
    
    # Aggregate positions by segment
    all_segments_df, small_segment_df, medium_segment_df, large_segment_df = aggregate_market_segments(
        event_id, market_slug, segment_map
    )
    
    if all_segments_df is None or all_segments_df.empty:
        print(f"  No data found, skipping.")
        return
    
    # Create output directory
    output_dir = SEGMENT_BASE / event_id / market_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write CSV files
    all_segments_df.to_csv(output_dir / "all_segments.csv", index=False)
    small_segment_df.to_csv(output_dir / "small_segment.csv", index=False)
    medium_segment_df.to_csv(output_dir / "medium_segment.csv", index=False)
    large_segment_df.to_csv(output_dir / "large_segment.csv", index=False)
    
    print(f"  Created 4 CSV files in {output_dir}")
    
    # Load price data
    price_df = load_price_odds(event_id, market_slug)
    
    # Create comparison graph
    plot_odds_comparison(
        event_id, market_slug,
        price_df,
        all_segments_df, small_segment_df, medium_segment_df, large_segment_df
    )


def main():
    """Main function: process all markets."""
    print("Building segment aggregation files and comparison graphs...\n")
    
    # Load segment mapping
    segment_map = load_segment_mapping()
    
    if not segment_map:
        print("Error: No segment mappings found. Exiting.")
        return
    
    # Iterate over all markets
    if not SEGMENT_OUTPUT_BASE.exists():
        print(f"Error: Segment output directory not found: {SEGMENT_OUTPUT_BASE}")
        return
    
    markets_processed = 0
    for event_dir in sorted(SEGMENT_OUTPUT_BASE.iterdir()):
        if not event_dir.is_dir() or event_dir.name.startswith("."):
            continue
        
        event_id = event_dir.name
        
        for market_dir in sorted(event_dir.iterdir()):
            if not market_dir.is_dir():
                continue
            
            market_slug = market_dir.name
            process_market(event_id, market_slug, segment_map)
            markets_processed += 1
    
    print(f"\n\nDone! Processed {markets_processed} markets.")
    print(f"Output written under: {SEGMENT_BASE}")


if __name__ == "__main__":
    main()

