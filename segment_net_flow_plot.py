#!/usr/bin/env python3
"""
Generate segment-wise cumulative net flow plot over time.
Compares how Small, Medium, and Large users buy or sell over time across all markets.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# Configuration
RAW_DIR = Path("raw")
SEGMENTS_FILE = Path("segmentation_results/user_segments.csv")
OUTPUT_DIR = Path("plots")
PLOT_FILE = OUTPUT_DIR / "segment_net_flow.png"
DATA_FILE = OUTPUT_DIR / "segment_daily_net_flow.csv"

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
    print(f"Segment distribution:")
    print(segments_df['segment'].value_counts())
    
    return segments_df

def preprocess_trades(trades_df):
    """Preprocess trades data: convert timestamp, extract trade_date."""
    print("\nPreprocessing trades data...")
    
    # Convert timestamp to datetime
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'], unit='s')
    
    # Extract trade_date (daily granularity)
    trades_df['trade_date'] = trades_df['timestamp'].dt.floor('D')
    
    print(f"Date range: {trades_df['trade_date'].min()} to {trades_df['trade_date'].max()}")
    
    return trades_df

def merge_with_segments(trades_df, segments_df):
    """Merge trades with user segments."""
    print("\nMerging trades with user segments...")
    
    # Merge on user_id
    merged_df = trades_df.merge(segments_df, on='user_id', how='inner')
    
    print(f"Trades after merge: {len(merged_df):,}")
    print(f"Trades dropped (no segment): {len(trades_df) - len(merged_df):,}")
    
    return merged_df

def compute_net_flow(trades_df):
    """Compute net flow per trade."""
    print("\nComputing net flow per trade...")
    
    # Compute net flow: BUY = +, SELL = -
    trades_df['net_flow'] = np.where(
        trades_df['side'] == 'BUY',
        trades_df['shares'] * trades_df['price'],
        -(trades_df['shares'] * trades_df['price'])
    )
    
    return trades_df

def aggregate_by_date_segment(trades_df):
    """Aggregate net flow by date and segment."""
    print("\nAggregating by date and segment...")
    
    # Calculate trade amounts
    trades_df['trade_amount'] = trades_df['shares'] * trades_df['price']
    
    # Group by trade_date and segment
    grouped = trades_df.groupby(['trade_date', 'segment']).agg({
        'net_flow': 'sum',
        'side': 'count'
    }).reset_index()
    
    # Rename columns
    grouped = grouped.rename(columns={
        'net_flow': 'daily_net_flow',
        'side': 'trade_count'
    })
    
    # Calculate daily_buy and daily_sell separately
    buy_trades = trades_df[trades_df['side'] == 'BUY'].groupby(['trade_date', 'segment']).agg({
        'trade_amount': 'sum'
    }).reset_index()
    buy_trades = buy_trades.rename(columns={'trade_amount': 'daily_buy'})
    
    sell_trades = trades_df[trades_df['side'] == 'SELL'].groupby(['trade_date', 'segment']).agg({
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
    aggregated = aggregated[['date', 'segment', 'daily_net_flow', 'daily_buy', 'daily_sell', 'trade_count']]
    
    print(f"Aggregated to {len(aggregated):,} date-segment combinations")
    
    return aggregated

def compute_cumulative_net_flow(aggregated_df):
    """Compute cumulative net flow for each segment."""
    print("\nComputing cumulative net flow...")
    
    # Sort by date
    aggregated_df = aggregated_df.sort_values(['segment', 'date']).reset_index(drop=True)
    
    # Compute cumulative net flow for each segment independently
    aggregated_df['cum_net_flow'] = aggregated_df.groupby('segment')['daily_net_flow'].cumsum()
    
    return aggregated_df

def create_plot(aggregated_df):
    """Create the segment-wise cumulative net flow plot."""
    print("\nCreating plot...")
    
    # Set up the plot
    plt.figure(figsize=(14, 8))
    
    # Define colors for each segment
    colors = {
        'Small': '#2E86AB',    # Blue
        'Medium': '#A23B72',   # Purple
        'Large': '#F18F01'     # Orange
    }
    
    # Plot each segment
    for segment in ['Small', 'Medium', 'Large']:
        segment_data = aggregated_df[aggregated_df['segment'] == segment].copy()
        
        if len(segment_data) == 0:
            continue
        
        # Sort by date
        segment_data = segment_data.sort_values('date')
        
        # Optional: Smooth with rolling mean (window=7 days)
        segment_data['cum_net_flow_smooth'] = segment_data['cum_net_flow'].rolling(
            window=7, min_periods=1, center=True
        ).mean()
        
        # Plot both raw and smoothed
        plt.plot(
            segment_data['date'],
            segment_data['cum_net_flow'],
            label=segment,
            color=colors[segment],
            linewidth=2,
            alpha=0.7
        )
        
        # Plot smoothed line (thicker, more visible)
        plt.plot(
            segment_data['date'],
            segment_data['cum_net_flow_smooth'],
            color=colors[segment],
            linewidth=3,
            alpha=0.9,
            linestyle='--'
        )
    
    # Formatting
    plt.title('Segment-Wise Cumulative Net Flow Over Time', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Cumulative Net Flow ($)', fontsize=12)
    plt.legend(loc='best', fontsize=11)
    plt.grid(True, alpha=0.3, linestyle='--')
    
    # Format x-axis dates
    plt.gcf().autofmt_xdate()
    
    # Add zero line
    plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
    
    plt.tight_layout()
    
    return plt

def main():
    """Main execution function."""
    print("=" * 60)
    print("Segment-Wise Net Flow Plot Generation")
    print("=" * 60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Step 1: Load all trades data
    trades_df = load_all_trades()
    
    # Step 2: Load user segments
    segments_df = load_user_segments()
    
    # Step 3: Preprocess trades
    trades_df = preprocess_trades(trades_df)
    
    # Step 4: Merge with segments
    trades_df = merge_with_segments(trades_df, segments_df)
    
    # Step 5: Compute net flow per trade
    trades_df = compute_net_flow(trades_df)
    
    # Step 6: Aggregate by date and segment
    aggregated_df = aggregate_by_date_segment(trades_df)
    
    # Step 7: Compute cumulative net flow
    aggregated_df = compute_cumulative_net_flow(aggregated_df)
    
    # Step 8: Create plot
    plt = create_plot(aggregated_df)
    
    # Step 9: Save outputs
    print(f"\nSaving plot to {PLOT_FILE}...")
    plt.savefig(PLOT_FILE, dpi=300, bbox_inches='tight')
    print(f"Plot saved successfully")
    
    print(f"\nSaving aggregated data to {DATA_FILE}...")
    aggregated_df.to_csv(DATA_FILE, index=False)
    print(f"Data saved successfully")
    
    # Print summary statistics
    print("\n" + "=" * 60)
    print("Summary Statistics")
    print("=" * 60)
    
    for segment in ['Small', 'Medium', 'Large']:
        segment_data = aggregated_df[aggregated_df['segment'] == segment]
        if len(segment_data) > 0:
            final_cum = segment_data['cum_net_flow'].iloc[-1]
            total_buy = segment_data['daily_buy'].sum()
            total_sell = segment_data['daily_sell'].sum()
            total_trades = segment_data['trade_count'].sum()
            
            print(f"\n{segment} Segment:")
            print(f"  Final Cumulative Net Flow: ${final_cum:,.2f}")
            print(f"  Total Buy: ${total_buy:,.2f}")
            print(f"  Total Sell: ${total_sell:,.2f}")
            print(f"  Total Trades: {total_trades:,}")
            print(f"  Trading Days: {len(segment_data)}")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

