#!/usr/bin/env python3
"""
Process senate market trades data to compute per-user statistics.
Filters events to keep only senate-related markets and generates output CSVs.
"""

import os
import shutil
import pandas as pd
from pathlib import Path
from collections import defaultdict

# Configuration
RAW_DIR = Path("raw")
OUTPUT_DIR = Path("output")
COMBINED_DIR = OUTPUT_DIR / "combined"

def filter_senate_events(raw_dir):
    """Filter events to keep only those with 'senate' in folder name (case-insensitive)."""
    senate_events = []
    events_to_delete = []
    
    if not raw_dir.exists():
        print(f"Error: {raw_dir} does not exist")
        return senate_events
    
    for item in raw_dir.iterdir():
        if item.is_dir():
            folder_name_lower = item.name.lower()
            if "senate" in folder_name_lower:
                senate_events.append(item)
                print(f"Keeping senate event: {item.name}")
            else:
                events_to_delete.append(item)
    
    # Delete non-senate events
    print(f"\nDeleting {len(events_to_delete)} non-senate events...")
    for event_dir in events_to_delete:
        print(f"  Deleting: {event_dir.name}")
        shutil.rmtree(event_dir)
    
    print(f"\nKept {len(senate_events)} senate events")
    return senate_events

def process_trades_csv(trades_file, market_id):
    """Process a single trades CSV file and compute per-user statistics."""
    try:
        df = pd.read_csv(trades_file)
        
        if df.empty:
            print(f"  Warning: {trades_file.name} is empty")
            return pd.DataFrame()
        
        # Ensure required columns exist
        required_cols = ['proxyWallet', 'side', 'size', 'price', 'slug']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"  Warning: {trades_file.name} missing columns: {missing_cols}")
            return pd.DataFrame()
        
        # Use slug from CSV as market_id (in case it differs)
        if 'slug' in df.columns and not df['slug'].empty:
            market_id = df['slug'].iloc[0]
        
        # Group by user_id (proxyWallet)
        user_stats = []
        
        for user_id, group in df.groupby('proxyWallet'):
            # Filter BUY and SELL trades
            buy_trades = group[group['side'] == 'BUY']
            sell_trades = group[group['side'] == 'SELL']
            
            # Calculate total buy amount (size * price)
            total_buy = (buy_trades['size'] * buy_trades['price']).sum()
            
            # Calculate total sell amount (size * price)
            total_sell = (sell_trades['size'] * sell_trades['price']).sum()
            
            # Calculate net amount
            net_amount = total_buy - total_sell
            
            # Count number of trades
            num_trades = len(group)
            
            user_stats.append({
                'market_id': market_id,
                'user_id': user_id,
                'total_buy': total_buy,
                'total_sell': total_sell,
                'net_amount': net_amount,
                'num_trades': num_trades
            })
        
        return pd.DataFrame(user_stats)
    
    except Exception as e:
        print(f"  Error processing {trades_file.name}: {e}")
        return pd.DataFrame()

def process_event(event_dir, output_base_dir):
    """Process all trades files in an event directory."""
    event_slug = event_dir.name
    trades_dir = event_dir / "trades"
    
    if not trades_dir.exists():
        print(f"  Warning: No trades directory found for {event_slug}")
        return []
    
    # Create output directory for this event
    event_output_dir = output_base_dir / event_slug
    event_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all trades CSV files
    trades_files = list(trades_dir.glob("*_trades.csv"))
    
    if not trades_files:
        print(f"  Warning: No trades CSV files found in {event_slug}")
        return []
    
    print(f"  Processing {len(trades_files)} market(s) in {event_slug}")
    
    all_user_stats = []
    
    for trades_file in trades_files:
        # Extract market slug from filename (remove _trades.csv suffix)
        market_slug = trades_file.stem.replace('_trades', '')
        
        print(f"    Processing market: {market_slug}")
        
        # Process trades and compute user statistics
        user_stats_df = process_trades_csv(trades_file, market_slug)
        
        if not user_stats_df.empty:
            # Save per-market CSV
            output_file = event_output_dir / f"{market_slug}_user_stats.csv"
            user_stats_df.to_csv(output_file, index=False)
            print(f"      Saved: {output_file.name} ({len(user_stats_df)} users)")
            
            # Collect for combined stats
            all_user_stats.append(user_stats_df)
    
    return all_user_stats

def generate_combined_stats(all_user_stats_list, combined_dir):
    """Generate combined user statistics across all markets."""
    if not all_user_stats_list:
        print("Warning: No user statistics to combine")
        return
    
    # Combine all user stats
    combined_df = pd.concat(all_user_stats_list, ignore_index=True)
    
    # Aggregate by user_id across all markets
    user_global_stats = []
    
    for user_id, group in combined_df.groupby('user_id'):
        total_buy = group['total_buy'].sum()
        total_sell = group['total_sell'].sum()
        net_amount = total_buy - total_sell
        num_trades = group['num_trades'].sum()
        num_markets = len(group)  # Number of unique markets this user traded in
        
        user_global_stats.append({
            'user_id': user_id,
            'total_buy': total_buy,
            'total_sell': total_sell,
            'net_amount': net_amount,
            'num_trades': num_trades,
            'num_markets': num_markets
        })
    
    global_stats_df = pd.DataFrame(user_global_stats)
    
    # Save combined stats
    combined_dir.mkdir(parents=True, exist_ok=True)
    output_file = combined_dir / "user_global_senate_stats.csv"
    global_stats_df.to_csv(output_file, index=False)
    print(f"\nSaved combined stats: {output_file} ({len(global_stats_df)} unique users)")

def main():
    """Main execution function."""
    print("=" * 60)
    print("Senate Market User Analysis")
    print("=" * 60)
    
    # Step 1: Filter senate events
    print("\nStep 1: Filtering senate events...")
    senate_events = filter_senate_events(RAW_DIR)
    
    if not senate_events:
        print("No senate events found. Exiting.")
        return
    
    # Step 2: Process trades and compute statistics
    print("\nStep 2: Processing trades and computing statistics...")
    all_user_stats_list = []
    
    for event_dir in senate_events:
        print(f"\nProcessing event: {event_dir.name}")
        user_stats_list = process_event(event_dir, OUTPUT_DIR)
        all_user_stats_list.extend(user_stats_list)
    
    # Step 3: Generate combined statistics
    print("\nStep 3: Generating combined statistics...")
    generate_combined_stats(all_user_stats_list, COMBINED_DIR)
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()

