#!/usr/bin/env python3
"""
Clean segment statistics CSV by removing columns with zeros and non-useful columns.
Add column descriptions.
"""

import pandas as pd
from pathlib import Path

INPUT_FILE = Path("segmentation_results/segment_statistics.csv")
OUTPUT_FILE = Path("segmentation_results/segment_statistics_cleaned.csv")
DESCRIPTIONS_FILE = Path("segmentation_results/column_descriptions.txt")

def analyze_columns(df):
    """Analyze which columns have zeros or constant values."""
    print("Analyzing columns...")
    columns_to_remove = []
    columns_to_keep = []
    
    for col in df.columns:
        if col == 'segment':
            columns_to_keep.append(col)
            continue
        
        # Check if column has all zeros
        if (df[col] == 0).all():
            print(f"  {col}: All zeros - REMOVE")
            columns_to_remove.append(col)
        # Check if column is constant (same value for all rows)
        elif df[col].nunique() == 1:
            print(f"  {col}: Constant value ({df[col].iloc[0]}) - REMOVE")
            columns_to_remove.append(col)
        else:
            columns_to_keep.append(col)
            print(f"  {col}: Has variation - KEEP")
    
    return columns_to_remove, columns_to_keep

def clean_dataframe(df):
    """Remove unwanted columns."""
    # Remove avg_trade_size as requested
    if 'avg_trade_size' in df.columns:
        df = df.drop(columns=['avg_trade_size'])
    
    # Remove columns with all zeros or constant values
    columns_to_remove, columns_to_keep = analyze_columns(df)
    
    # Also remove columns that don't provide useful insights
    # Keep: segment, num_users, pct_of_total, and meaningful stats
    # Remove: redundant or less useful columns
    
    # Remove columns with all zeros or constant values
    for col in df.columns:
        if col == 'segment':
            continue
        # Remove if all values are exactly 0
        if (df[col] == 0).all():
            if col in df.columns:
                df = df.drop(columns=[col])
        # Remove if constant value (same for all segments)
        elif df[col].nunique() == 1:
            if col in df.columns:
                df = df.drop(columns=[col])
    
    # Remove std columns as they're less commonly used for insights
    std_cols = [col for col in df.columns if col.endswith('_std')]
    df = df.drop(columns=std_cols)
    
    # Define columns to keep (prioritize most useful metrics)
    essential_columns = [
        'segment',
        'num_users',
        'pct_of_total',
        'total_buy_avg',
        'total_buy_median',
        'total_buy_max',
        'total_buy_sum',
        'total_sell_avg',
        'total_sell_median',
        'total_sell_max',
        'total_sell_sum',
        'net_amount_avg',
        'net_amount_median',
        'net_amount_min',
        'net_amount_max',
        'net_amount_sum',
        'num_trades_avg',
        'num_trades_median',
        'num_trades_min',
        'num_trades_max',
        'num_trades_sum',
        'num_markets_avg',
        'num_markets_max',
        'total_volume_avg',
        'total_volume_sum'
    ]
    
    # Keep only columns that exist and are in our essential list
    columns_to_keep = [col for col in essential_columns if col in df.columns]
    
    df_cleaned = df[columns_to_keep].copy()
    
    return df_cleaned

def generate_descriptions():
    """Generate descriptions for each column."""
    descriptions = {
        'segment': 'User segment category: Small (0-50th percentile), Medium (50-90th percentile), or Large (90-100th percentile)',
        'num_users': 'Number of users in this segment',
        'pct_of_total': 'Percentage of total users represented by this segment',
        'total_buy_avg': 'Average total buy amount per user (sum of shares × price for all BUY trades)',
        'total_buy_median': 'Median total buy amount per user (middle value when sorted)',
        'total_buy_min': 'Minimum total buy amount among users in this segment',
        'total_buy_max': 'Maximum total buy amount among users in this segment',
        'total_buy_sum': 'Total buy amount across all users in this segment',
        'total_sell_avg': 'Average total sell amount per user (sum of shares × price for all SELL trades)',
        'total_sell_median': 'Median total sell amount per user (middle value when sorted)',
        'total_sell_min': 'Minimum total sell amount among users in this segment',
        'total_sell_max': 'Maximum total sell amount among users in this segment',
        'total_sell_sum': 'Total sell amount across all users in this segment',
        'net_amount_avg': 'Average net amount per user (total_buy - total_sell). Positive = net buyer, Negative = net seller',
        'net_amount_median': 'Median net amount per user (middle value when sorted)',
        'net_amount_min': 'Minimum net amount among users in this segment',
        'net_amount_max': 'Maximum net amount among users in this segment',
        'net_amount_sum': 'Total net amount across all users in this segment',
        'num_trades_avg': 'Average number of trades per user in this segment',
        'num_trades_median': 'Median number of trades per user (middle value when sorted)',
        'num_trades_min': 'Minimum number of trades among users in this segment',
        'num_trades_max': 'Maximum number of trades among users in this segment',
        'num_trades_sum': 'Total number of trades across all users in this segment',
        'num_markets_avg': 'Average number of different markets each user traded in',
        'num_markets_median': 'Median number of markets per user (middle value when sorted)',
        'num_markets_max': 'Maximum number of markets any user in this segment traded in',
        'total_volume_avg': 'Average total trading volume per user (total_buy + total_sell)',
        'total_volume_sum': 'Total trading volume across all users in this segment'
    }
    return descriptions

def main():
    """Main execution."""
    print("=" * 60)
    print("Cleaning Segment Statistics")
    print("=" * 60)
    
    # Load data
    print(f"\nLoading {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    print(f"Original columns: {len(df.columns)}")
    
    # Clean dataframe
    print("\nCleaning dataframe...")
    df_cleaned = clean_dataframe(df)
    print(f"Cleaned columns: {len(df_cleaned.columns)}")
    
    # Save cleaned CSV
    df_cleaned.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved cleaned data to: {OUTPUT_FILE}")
    
    # Generate and save descriptions
    descriptions = generate_descriptions()
    with open(DESCRIPTIONS_FILE, 'w') as f:
        f.write("Column Descriptions for segment_statistics_cleaned.csv\n")
        f.write("=" * 60 + "\n\n")
        for col in df_cleaned.columns:
            if col in descriptions:
                f.write(f"{col}:\n")
                f.write(f"  {descriptions[col]}\n\n")
            else:
                f.write(f"{col}:\n")
                f.write(f"  (Description not available)\n\n")
    
    print(f"Saved column descriptions to: {DESCRIPTIONS_FILE}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"\nRemoved columns: {len(df.columns) - len(df_cleaned.columns)}")
    print(f"Kept columns: {len(df_cleaned.columns)}")
    print("\nKept columns:")
    for col in df_cleaned.columns:
        print(f"  - {col}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()

