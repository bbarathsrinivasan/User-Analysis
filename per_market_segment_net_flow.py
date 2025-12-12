#!/usr/bin/env python3
"""
Generate per-market segment-wise daily net flow plots.
Each market gets its own plot showing daily net flow (not cumulative) for Small, Medium, and Large segments.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# Configuration
RAW_DIR = Path("raw")
SEGMENTS_FILE = Path("segmentation_results/user_segments.csv")
OUTPUT_PLOTS_DIR = Path("user_plots/segment_net_flow")
OUTPUT_DATA_DIR = Path("user_plots/segment_daily_net_flow")

def load_all_trades():
    """Load and combine all trades CSV files from all senate markets."""
    print("Loading trades data from all markets...")
    
    all_trades = []
    event_dirs = [d for d in RAW_DIR.iterdir() if d.is_dir()]
    
    for event_dir in sorted(event_dirs):
        trades_dir = event_dir / "trades"
        
        if not trades_dir.exists():
            continue
        
        trades_files = list(trades_dir.glob("*_trades.csv"))
        
        for trades_file in trades_files:
            try:
                df = pd.read_csv(trades_file, low_memory=False)
                
                if df.empty:
                    continue
                
                # Ensure required columns exist
                required_cols = ['proxyWallet', 'side', 'size', 'price', 'timestamp', 'slug']
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    continue
                
                # Rename columns
                df = df.rename(columns={
                    'proxyWallet': 'user_id',
                    'size': 'shares',
                    'slug': 'market_id'
                })
                
                # Keep only necessary columns
                df = df[['user_id', 'side', 'shares', 'price', 'timestamp', 'market_id']].copy()
                
                all_trades.append(df)
                
            except Exception as e:
                print(f"  Warning: Error loading {trades_file.name}: {e}")
                continue
    
    if not all_trades:
        raise ValueError("No trades data found")
    
    trades_df = pd.concat(all_trades, ignore_index=True)
    print(f"Loaded {len(trades_df):,} trades from {len(all_trades)} market files")
    
    return trades_df

def load_user_segments():
    """Load user segmentation data."""
    print(f"\nLoading user segments from {SEGMENTS_FILE}...")
    
    segments_df = pd.read_csv(SEGMENTS_FILE)
    segments_df = segments_df[['user_id', 'segment']].copy()
    
    print(f"Loaded {len(segments_df):,} user segments")
    
    return segments_df

def preprocess_trades(trades_df):
    """Preprocess trades data: convert timestamp, extract trade_date."""
    # Convert timestamp to datetime
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], unit='s')
    
    # Extract trade_date (daily granularity)
    trades_df['trade_date'] = trades_df['timestamp'].dt.floor('D')
    
    return trades_df

def merge_with_segments(trades_df, segments_df):
    """Merge trades with user segments."""
    # Merge on user_id
    merged_df = trades_df.merge(segments_df, on='user_id', how='inner')
    
    return merged_df

def compute_net_flow(trades_df):
    """Compute net flow per trade."""
    # Compute net flow: BUY = +, SELL = -
    trades_df['net_flow'] = np.where(
        trades_df['side'] == 'BUY',
        trades_df['shares'] * trades_df['price'],
        -(trades_df['shares'] * trades_df['price'])
    )
    
    return trades_df

def aggregate_market_daily(trades_df, market_id):
    """Aggregate daily net flow by segment for a specific market."""
    # Filter trades for this market
    market_trades = trades_df[trades_df['market_id'] == market_id].copy()
    
    if market_trades.empty:
        return None
    
    # Calculate trade amounts
    market_trades['trade_amount'] = market_trades['shares'] * market_trades['price']
    
    # Group by trade_date and segment
    grouped = market_trades.groupby(['trade_date', 'segment']).agg({
        'net_flow': 'sum',
        'side': 'count'
    }).reset_index()
    
    # Rename columns
    grouped = grouped.rename(columns={
        'net_flow': 'daily_net',
        'side': 'trade_count'
    })
    
    # Calculate daily_buy and daily_sell separately
    buy_trades = market_trades[market_trades['side'] == 'BUY'].groupby(['trade_date', 'segment']).agg({
        'trade_amount': 'sum'
    }).reset_index()
    buy_trades = buy_trades.rename(columns={'trade_amount': 'daily_buy'})
    
    sell_trades = market_trades[market_trades['side'] == 'SELL'].groupby(['trade_date', 'segment']).agg({
        'trade_amount': 'sum'
    }).reset_index()
    sell_trades = sell_trades.rename(columns={'trade_amount': 'daily_sell'})
    
    # Merge buy and sell
    aggregated = grouped.merge(buy_trades, on=['trade_date', 'segment'], how='left')
    aggregated = aggregated.merge(sell_trades, on=['trade_date', 'segment'], how='left')
    
    # Fill NaN with 0
    aggregated['daily_buy'] = aggregated['daily_buy'].fillna(0)
    aggregated['daily_sell'] = aggregated['daily_sell'].fillna(0)
    
    # Rename trade_date to date
    aggregated = aggregated.rename(columns={'trade_date': 'date'})
    
    # Reorder columns
    aggregated = aggregated[['date', 'segment', 'daily_net', 'daily_buy', 'daily_sell', 'trade_count']]
    
    # Sort by date
    aggregated = aggregated.sort_values('date').reset_index(drop=True)
    
    return aggregated

def create_market_plot(aggregated_df, market_id):
    """Create the segment-wise daily net flow plot for a market."""
    # Set up the plot
    plt.figure(figsize=(14, 8))
    
    # Define colors for each segment
    colors = {
        'Small': '#2E86AB',    # Blue
        'Medium': '#A23B72',   # Purple
        'Large': '#F18F01'     # Orange
    }
    
    # Check if we should use log scale (only if all values are positive)
    use_log_scale = True
    min_net_flow = aggregated_df['daily_net'].min()
    if min_net_flow <= 0:
        use_log_scale = False
    
    # Plot each segment
    for segment in ['Small', 'Medium', 'Large']:
        segment_data = aggregated_df[aggregated_df['segment'] == segment].copy()
        
        if len(segment_data) == 0:
            continue
        
        # Sort by date
        segment_data = segment_data.sort_values('date')
        
        # Plot daily net flow
        plt.plot(
            segment_data['date'],
            segment_data['daily_net'],
            label=segment,
            color=colors[segment],
            linewidth=2.5,
            marker='o',
            markersize=4,
            alpha=0.8
        )
    
    # Formatting
    plt.title(f'Segment-Wise Daily Net Flow — Market {market_id}', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=12)
    
    # Apply log scale if appropriate
    if use_log_scale:
        plt.yscale('log')
        plt.ylabel('Daily Net Flow ($) - Log Scale', fontsize=12)
    else:
        plt.ylabel('Daily Net Flow ($)', fontsize=12)
        # Add zero line
        plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
    
    plt.legend(loc='best', fontsize=11)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # Format x-axis dates
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    
    return plt

def process_all_markets(trades_df):
    """Process all markets and generate plots."""
    # Get unique market IDs
    market_ids = sorted(trades_df['market_id'].unique())
    
    print(f"\nProcessing {len(market_ids)} markets...")
    
    market_stats = []
    
    for i, market_id in enumerate(market_ids, 1):
        print(f"  [{i}/{len(market_ids)}] Processing market: {market_id}")
        
        # Aggregate daily data for this market
        aggregated_df = aggregate_market_daily(trades_df, market_id)
        
        if aggregated_df is None or aggregated_df.empty:
            print(f"    Warning: No data for market {market_id}")
            continue
        
        # Create plot
        plt = create_market_plot(aggregated_df, market_id)
        
        # Save plot
        plot_file = OUTPUT_PLOTS_DIR / f"{market_id}.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        # Save data
        data_file = OUTPUT_DATA_DIR / f"{market_id}.csv"
        aggregated_df.to_csv(data_file, index=False)
        
        # Collect statistics
        stats = {
            'market_id': market_id,
            'num_days': len(aggregated_df['date'].unique()),
            'date_range': (aggregated_df['date'].min(), aggregated_df['date'].max()),
            'total_trades': aggregated_df['trade_count'].sum(),
            'small_net': aggregated_df[aggregated_df['segment'] == 'Small']['daily_net'].sum() if 'Small' in aggregated_df['segment'].values else 0,
            'medium_net': aggregated_df[aggregated_df['segment'] == 'Medium']['daily_net'].sum() if 'Medium' in aggregated_df['segment'].values else 0,
            'large_net': aggregated_df[aggregated_df['segment'] == 'Large']['daily_net'].sum() if 'Large' in aggregated_df['segment'].values else 0,
        }
        market_stats.append(stats)
    
    return market_stats

def main():
    """Main execution function."""
    print("=" * 60)
    print("Per-Market Segment-Wise Daily Net Flow Plot Generation")
    print("=" * 60)
    
    # Create output directories
    OUTPUT_PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load all trades data
    trades_df = load_all_trades()
    
    # Step 2: Load user segments
    segments_df = load_user_segments()
    
    # Step 3: Preprocess trades
    trades_df = preprocess_trades(trades_df)
    
    # Step 4: Merge with segments
    trades_df = merge_with_segments(trades_df, segments_df)
    print(f"\nTrades after merge: {len(trades_df):,}")
    
    # Step 5: Compute net flow per trade
    trades_df = compute_net_flow(trades_df)
    
    # Step 6: Process all markets
    market_stats = process_all_markets(trades_df)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total Markets Processed: {len(market_stats)}")
    print(f"Total Plots Generated: {len(market_stats)}")
    print(f"Total CSV Files Generated: {len(market_stats)}")
    print(f"\nPlots saved to: {OUTPUT_PLOTS_DIR}")
    print(f"Data saved to: {OUTPUT_DATA_DIR}")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    
    return market_stats

if __name__ == "__main__":
    main()

