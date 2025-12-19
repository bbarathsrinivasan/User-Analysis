"""
Script to calculate daily closing prices for each market.
For each day, finds the last price (closing price) and saves it to a CSV file.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime


def calculate_closing_prices_for_market(price_file_path, output_file_path):
    """
    Calculate daily closing prices for a market price file.
    
    Args:
        price_file_path: Path to the input price CSV file
        output_file_path: Path to save the output CSV file with closing prices
    """
    try:
        # Read the price file
        df = pd.read_csv(price_file_path, low_memory=False)
        
        if df.empty:
            print(f"  Warning: Empty price file: {price_file_path}")
            return False
        
        # Convert timestamp to numeric and datetime
        df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        
        if df.empty:
            print(f"  Warning: No valid timestamps in: {price_file_path}")
            return False
        
        # Convert timestamp to datetime and extract date
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
        df['date'] = df['datetime'].dt.date
        
        # Map token_id to YES/NO based on order of first appearance
        # First token_id = YES, second token_id = NO
        unique_token_ids = df['token_id'].drop_duplicates().tolist()
        token_id_to_type = {}
        if len(unique_token_ids) >= 1:
            token_id_to_type[unique_token_ids[0]] = 'YES'
        if len(unique_token_ids) >= 2:
            token_id_to_type[unique_token_ids[1]] = 'NO'
        
        # Group by date and token_id, then get the last price (closing price) for each day
        # Sort by timestamp first to ensure we get the last price of the day
        df_sorted = df.sort_values('timestamp')
        
        # Get closing price for each date and token_id combination
        closing_prices = df_sorted.groupby(['date', 'token_id']).last().reset_index()
        
        # Map token_id to token_type (YES/NO)
        closing_prices['token_type'] = closing_prices['token_id'].map(token_id_to_type)
        
        # Select columns: date, token_type, closing_price
        closing_df = closing_prices[['date', 'token_type', 'price']].copy()
        closing_df.columns = ['date', 'token_type', 'closing_price']
        
        # Sort by date, then by token_type (YES first, then NO)
        closing_df = closing_df.sort_values(['date', 'token_type'])
        
        # Save to CSV
        closing_df.to_csv(output_file_path, index=False)
        
        return True
        
    except Exception as e:
        print(f"  Error processing {price_file_path}: {str(e)}")
        return False


def process_all_markets(base_path="raw"):
    """
    Process all price files and calculate closing prices for each market.
    
    Args:
        base_path: Base path to raw data directory (default: "raw")
    """
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"Error: Raw data directory not found at {base_path}")
        return
    
    # Find all event directories
    event_dirs = [d for d in base_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not event_dirs:
        print(f"Warning: No event directories found in {base_path}")
        return
    
    print(f"Found {len(event_dirs)} event(s) to process")
    
    total_files = 0
    processed_files = 0
    
    # Process each event
    for event_dir in sorted(event_dirs):
        event_id = event_dir.name
        prices_dir = event_dir / "prices"
        
        if not prices_dir.exists():
            print(f"  Warning: No prices directory found for event {event_id}")
            continue
        
        # Find all price CSV files
        price_files = list(prices_dir.glob("*_price.csv"))
        
        if not price_files:
            print(f"  Warning: No price CSV files found for event {event_id}")
            continue
        
        print(f"Processing event {event_id} ({len(price_files)} price file(s))...")
        
        # Process each price file
        for price_file in sorted(price_files):
            total_files += 1
            
            # Create output filename (replace _price.csv with _closing_prices.csv)
            market_slug = price_file.stem.replace('_price', '')
            output_file = prices_dir / f"{market_slug}_closing_prices.csv"
            
            if calculate_closing_prices_for_market(price_file, output_file):
                processed_files += 1
                print(f"  ✓ Generated closing prices for {market_slug}")
            else:
                print(f"  ✗ Failed to process {market_slug}")
    
    print(f"\nCompleted: {processed_files}/{total_files} price files processed successfully")


def main():
    """
    Main function to calculate closing prices for all markets.
    """
    print("Calculating daily closing prices for all markets...\n")
    process_all_markets(base_path="raw")
    print("\nDone!")


if __name__ == "__main__":
    main()
