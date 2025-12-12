#!/usr/bin/env python3
"""
Process trades data to create daily user investment files for each market.
Tracks user trading activity by day relative to market end date.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date
from collections import defaultdict

# Configuration
RAW_DIR = Path("raw")
OUTPUT_DIR = Path("user_trades")

def get_market_end_date(meta_file, trades_df):
    """Get market end date from meta CSV or use last trade timestamp."""
    market_end_date = None
    
    # Try to get from meta CSV
    if meta_file.exists():
        try:
            meta_df = pd.read_csv(meta_file)
            if 'market_endDate' in meta_df.columns:
                # Find the row for this market
                for idx, row in meta_df.iterrows():
                    end_date_str = row.get('market_endDate', '')
                    if pd.notna(end_date_str) and end_date_str != '':
                        try:
                            # Parse ISO format date
                            if 'T' in str(end_date_str):
                                market_end_date = datetime.fromisoformat(str(end_date_str).replace('Z', '+00:00')).date()
                            else:
                                market_end_date = datetime.strptime(str(end_date_str), '%Y-%m-%d').date()
                            break
                        except:
                            continue
        except Exception as e:
            print(f"    Warning: Could not read meta file: {e}")
    
    # If not found in meta, use last trade timestamp
    if market_end_date is None:
        if not trades_df.empty and 'timestamp' in trades_df.columns:
            max_timestamp = trades_df['timestamp'].max()
            market_end_date = datetime.fromtimestamp(max_timestamp).date()
        else:
            raise ValueError("Cannot determine market end date: no meta data and no trades")
    
    return market_end_date

def process_market_trades(trades_file, event_slug, market_slug, meta_file):
    """Process trades for a single market and generate daily user investment files."""
    try:
        # Read trades data
        trades_df = pd.read_csv(trades_file)
        
        if trades_df.empty:
            print(f"    Warning: {trades_file.name} is empty")
            return None
        
        # Ensure required columns exist
        required_cols = ['proxyWallet', 'side', 'size', 'price', 'timestamp']
        missing_cols = [col for col in required_cols if col not in trades_df.columns]
        if missing_cols:
            print(f"    Warning: {trades_file.name} missing columns: {missing_cols}")
            return None
        
        # Get market end date
        market_end_date = get_market_end_date(meta_file, trades_df)
        
        # Convert timestamp to date and calculate day_index
        trades_df['trade_date'] = pd.to_datetime(trades_df['timestamp'], unit='s').dt.date
        # Calculate day_index: (trade_date - market_end_date).days
        # day_index = 0 is end day, negative values are days before end
        trades_df['day_index'] = trades_df['trade_date'].apply(lambda x: (x - market_end_date).days)
        
        # Filter out trades after end date (shouldn't exist, but handle edge cases)
        trades_df = trades_df[trades_df['day_index'] <= 0]
        
        if trades_df.empty:
            print(f"    Warning: No valid trades after filtering")
            return None
        
        # Calculate trade amounts
        trades_df['buy_amount'] = np.where(
            trades_df['side'] == 'BUY',
            trades_df['size'] * trades_df['price'],
            0
        )
        trades_df['sell_amount'] = np.where(
            trades_df['side'] == 'SELL',
            trades_df['size'] * trades_df['price'],
            0
        )
        
        # Create output directory
        output_market_dir = OUTPUT_DIR / event_slug / market_slug
        output_market_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each user
        user_stats = {}
        unique_users = trades_df['proxyWallet'].unique()
        
        for user_id in unique_users:
            user_trades = trades_df[trades_df['proxyWallet'] == user_id].copy()
            
            # Group by day_index
            daily_stats = []
            
            for day_idx, day_group in user_trades.groupby('day_index'):
                trade_date = day_group['trade_date'].iloc[0]
                
                daily_buy = day_group['buy_amount'].sum()
                daily_sell = day_group['sell_amount'].sum()
                daily_net = daily_buy - daily_sell
                trade_count = len(day_group)
                
                daily_stats.append({
                    'day_index': int(day_idx),
                    'date': trade_date,
                    'daily_buy': daily_buy,
                    'daily_sell': daily_sell,
                    'daily_net': daily_net,
                    'trade_count': trade_count
                })
            
            # Sort by day_index (ascending: most negative to 0)
            daily_stats.sort(key=lambda x: x['day_index'])
            
            # Save to CSV
            if daily_stats:
                user_df = pd.DataFrame(daily_stats)
                user_file = output_market_dir / f"{user_id}.csv"
                user_df.to_csv(user_file, index=False)
                user_stats[user_id] = {
                    'num_days': len(daily_stats),
                    'total_trades': user_trades.shape[0],
                    'day_range': (min(s['day_index'] for s in daily_stats), max(s['day_index'] for s in daily_stats))
                }
        
        # Return summary
        return {
            'market_slug': market_slug,
            'market_end_date': market_end_date,
            'num_users': len(user_stats),
            'total_trades': len(trades_df),
            'day_range': (trades_df['day_index'].min(), trades_df['day_index'].max()),
            'date_range': (trades_df['trade_date'].min(), trades_df['trade_date'].max()),
            'user_stats': user_stats
        }
    
    except Exception as e:
        print(f"    Error processing {trades_file.name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_event(event_dir):
    """Process all markets in an event."""
    event_slug = event_dir.name
    trades_dir = event_dir / "trades"
    meta_file = event_dir / "meta" / f"meta_{event_slug}.csv"
    
    if not trades_dir.exists():
        print(f"  Warning: No trades directory found for {event_slug}")
        return []
    
    # Find all trades CSV files
    trades_files = list(trades_dir.glob("*_trades.csv"))
    
    if not trades_files:
        print(f"  Warning: No trades CSV files found in {event_slug}")
        return []
    
    print(f"  Processing {len(trades_files)} market(s) in {event_slug}")
    
    market_summaries = []
    
    for trades_file in trades_files:
        # Extract market slug from filename (remove _trades.csv suffix)
        market_slug = trades_file.stem.replace('_trades', '')
        
        print(f"    Processing market: {market_slug}")
        
        summary = process_market_trades(trades_file, event_slug, market_slug, meta_file)
        
        if summary:
            market_summaries.append(summary)
            
            # Print summary
            print(f"      Market End Date: {summary['market_end_date']}")
            print(f"      Users: {summary['num_users']}")
            print(f"      Total Trades: {summary['total_trades']}")
            print(f"      Day Range: {summary['day_range'][0]} to {summary['day_range'][1]}")
            print(f"      Date Range: {summary['date_range'][0]} to {summary['date_range'][1]}")
    
    return market_summaries

def main():
    """Main execution function."""
    print("=" * 60)
    print("Daily User Investment Analysis")
    print("=" * 60)
    
    if not RAW_DIR.exists():
        print(f"Error: {RAW_DIR} does not exist")
        return
    
    # Get all event directories
    event_dirs = [d for d in RAW_DIR.iterdir() if d.is_dir()]
    
    if not event_dirs:
        print(f"No event directories found in {RAW_DIR}")
        return
    
    print(f"\nProcessing {len(event_dirs)} events...")
    
    all_summaries = []
    
    for event_dir in sorted(event_dirs):
        print(f"\nProcessing event: {event_dir.name}")
        summaries = process_event(event_dir)
        all_summaries.extend(summaries)
    
    # Print overall summary
    print("\n" + "=" * 60)
    print("Overall Summary")
    print("=" * 60)
    print(f"Total Markets Processed: {len(all_summaries)}")
    print(f"Total Users: {sum(s['num_users'] for s in all_summaries)}")
    print(f"Total Trades: {sum(s['total_trades'] for s in all_summaries)}")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("=" * 60)
    
    return all_summaries

if __name__ == "__main__":
    main()

