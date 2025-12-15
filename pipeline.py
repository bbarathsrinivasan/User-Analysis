"""
Main pipeline script for processing trade data.
"""
import pandas as pd
from pathlib import Path
from utils import (
    load_market_trades,
    convert_to_utc_date,
    compute_day_offset,
    aggregate_daily_trades,
    fill_missing_days_and_compute_cumulative,
    write_user_output,
    aggregate_all_markets_trades,
    compute_global_cumulative_position,
    write_all_markets_user_output
)


def process_market(event_id, market_slug, base_path="raw"):
    """
    Process a single market: load trades, compute aggregations, and write output files.
    
    Args:
        event_id: Event identifier
        market_slug: Market slug (used to identify the CSV file)
        base_path: Base path to raw data directory (default: "raw")
    
    Returns:
        DataFrame with processed market data (final_df) or None if processing failed
    """
    try:
        print(f"Processing event {event_id}, market {market_slug}...")
        
        # Load trade CSV file for this market
        df = load_market_trades(event_id, market_slug, base_path)
        
        if df.empty:
            print(f"  Warning: No trades found for event {event_id}, market {market_slug}")
            return None
        
        # Extract market_id and market_slug from the first row (should be consistent across all rows)
        market_id = df['market_id'].iloc[0]
        market_slug = df['market_slug'].iloc[0]
        
        # Convert unix_timestamp to UTC date
        df = convert_to_utc_date(df)
        
        # Compute day_offset
        df = compute_day_offset(df)
        
        # Aggregate daily trades
        aggregated_df = aggregate_daily_trades(df, event_id, market_id, market_slug)
        
        # Fill missing days and compute cumulative positions
        final_df = fill_missing_days_and_compute_cumulative(aggregated_df)
        
        # Get unique user_id and token_type combinations
        user_token_combinations = final_df[['user_id', 'token_type']].drop_duplicates()
        
        # Write output files for each user and token type
        for _, row in user_token_combinations.iterrows():
            user_id = row['user_id']
            token_type = row['token_type']
            write_user_output(final_df, user_id, event_id, market_id, token_type)
        
        print(f"  Completed: event {event_id}, market {market_slug}")
        
        return final_df
        
    except Exception as e:
        print(f"  Error processing event {event_id}, market {market_slug}: {str(e)}")
        raise


def main():
    """
    Main function that discovers all events and markets, then processes them sequentially.
    """
    base_path = "raw"
    events_path = Path(base_path)
    
    if not events_path.exists():
        print(f"Error: Raw data directory not found at {events_path}")
        print("Please ensure the 'raw' directory exists with the structure: raw/<event_id>/trades/*_trades.csv")
        return
    
    # Discover all event directories
    event_dirs = [d for d in events_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not event_dirs:
        print(f"Warning: No event directories found in {events_path}")
        return
    
    print(f"Found {len(event_dirs)} event(s) to process")
    
    total_markets = 0
    processed_markets = 0
    all_markets_data = []  # Store all market results for aggregation
    
    # Process each event
    for event_dir in sorted(event_dirs):
        event_id = event_dir.name
        
        # Check for trades directory
        trades_dir = event_dir / "trades"
        
        if not trades_dir.exists():
            print(f"  Warning: No trades directory found for event {event_id}")
            continue
        
        # Find all trade CSV files (ending with _trades.csv)
        trade_files = list(trades_dir.glob("*_trades.csv"))
        
        if not trade_files:
            print(f"  Warning: No trade CSV files found for event {event_id}")
            continue
        
        print(f"Processing event {event_id} ({len(trade_files)} market(s))...")
        
        # Process each market CSV file sequentially
        for trade_file in sorted(trade_files):
            # Extract market_slug from filename (remove _trades.csv suffix)
            market_slug = trade_file.stem.replace('_trades', '')
            total_markets += 1
            
            try:
                final_df = process_market(event_id, market_slug, base_path)
                if final_df is not None:
                    all_markets_data.append(final_df)
                    processed_markets += 1
            except Exception as e:
                print(f"  Failed to process event {event_id}, market {market_slug}: {str(e)}")
                # Continue with next market
                continue
    
    print(f"\nPipeline completed: {processed_markets}/{total_markets} markets processed successfully")
    
    # Generate aggregated output across all markets
    if all_markets_data:
        print("\nGenerating aggregated output across all markets...")
        try:
            # Concatenate all market DataFrames
            all_markets_df = pd.concat(all_markets_data, ignore_index=True)
            
            # Aggregate trades across all markets (sum daily_buy/daily_sell per event_id, market_id, day_offset)
            aggregated_df = aggregate_all_markets_trades(all_markets_df)
            
            # Compute global cumulative position
            final_aggregated_df = compute_global_cumulative_position(aggregated_df)
            
            # Get unique user_id and token_type combinations
            user_token_combinations = final_aggregated_df[['user_id', 'token_type']].drop_duplicates()
            
            # Write aggregated output files for each user and token type
            for _, row in user_token_combinations.iterrows():
                user_id = row['user_id']
                token_type = row['token_type']
                write_all_markets_user_output(final_aggregated_df, user_id, token_type)
            
            print(f"  Generated aggregated output for {len(user_token_combinations)} user/token combinations")
            
        except Exception as e:
            print(f"  Error generating aggregated output: {str(e)}")
            raise
    else:
        print("  No market data to aggregate")


if __name__ == "__main__":
    main()
