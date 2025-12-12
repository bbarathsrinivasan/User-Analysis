#!/usr/bin/env python3
"""
Segment users from global senate stats and generate detailed statistics for each segment.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
INPUT_FILE = Path("output/combined/user_global_senate_stats.csv")
OUTPUT_DIR = Path("segmentation_results")

def calculate_percentiles(df, column):
    """Calculate percentiles for a column."""
    return {
        'p25': df[column].quantile(0.25),
        'p50': df[column].quantile(0.50),  # median
        'p75': df[column].quantile(0.75),
        'p90': df[column].quantile(0.90),
        'p95': df[column].quantile(0.95),
        'p99': df[column].quantile(0.99)
    }

def segment_users(df):
    """Segment users into three categories: small, medium, and large based on trading volume."""
    df['total_volume'] = df['total_buy'] + df['total_sell']
    
    # Use 50th and 90th percentiles: small (0-50%), medium (50-90%), large (90-100%)
    p50 = df['total_volume'].quantile(0.50)
    p90 = df['total_volume'].quantile(0.90)
    
    def assign_segment(row):
        vol = row['total_volume']
        if vol <= p50:
            return 'Small'
        elif vol <= p90:
            return 'Medium'
        else:
            return 'Large'
    
    df['segment'] = df.apply(assign_segment, axis=1)
    return df

def generate_segment_stats(df, segment_column, output_file):
    """Generate detailed statistics for each segment."""
    segments = df[segment_column].unique()
    stats_list = []
    
    for segment in segments:
        segment_df = df[df[segment_column] == segment]
        
        stats = {
            'segment': segment,
            'num_users': len(segment_df),
            'pct_of_total': (len(segment_df) / len(df)) * 100,
            
            # Total Buy stats
            'total_buy_avg': segment_df['total_buy'].mean(),
            'total_buy_median': segment_df['total_buy'].median(),
            'total_buy_min': segment_df['total_buy'].min(),
            'total_buy_max': segment_df['total_buy'].max(),
            'total_buy_std': segment_df['total_buy'].std(),
            'total_buy_sum': segment_df['total_buy'].sum(),
            
            # Total Sell stats
            'total_sell_avg': segment_df['total_sell'].mean(),
            'total_sell_median': segment_df['total_sell'].median(),
            'total_sell_min': segment_df['total_sell'].min(),
            'total_sell_max': segment_df['total_sell'].max(),
            'total_sell_std': segment_df['total_sell'].std(),
            'total_sell_sum': segment_df['total_sell'].sum(),
            
            # Net Amount stats
            'net_amount_avg': segment_df['net_amount'].mean(),
            'net_amount_median': segment_df['net_amount'].median(),
            'net_amount_min': segment_df['net_amount'].min(),
            'net_amount_max': segment_df['net_amount'].max(),
            'net_amount_std': segment_df['net_amount'].std(),
            'net_amount_sum': segment_df['net_amount'].sum(),
            
            # Number of Trades stats
            'num_trades_avg': segment_df['num_trades'].mean(),
            'num_trades_median': segment_df['num_trades'].median(),
            'num_trades_min': segment_df['num_trades'].min(),
            'num_trades_max': segment_df['num_trades'].max(),
            'num_trades_std': segment_df['num_trades'].std(),
            'num_trades_sum': segment_df['num_trades'].sum(),
            
            # Number of Markets stats
            'num_markets_avg': segment_df['num_markets'].mean(),
            'num_markets_median': segment_df['num_markets'].median(),
            'num_markets_min': segment_df['num_markets'].min(),
            'num_markets_max': segment_df['num_markets'].max(),
            'num_markets_std': segment_df['num_markets'].std(),
            
            # Additional metrics
            'total_volume_avg': (segment_df['total_buy'] + segment_df['total_sell']).mean(),
            'total_volume_sum': (segment_df['total_buy'] + segment_df['total_sell']).sum(),
            'avg_trade_size': ((segment_df['total_buy'] + segment_df['total_sell']) / segment_df['num_trades']).mean(),
        }
        
        stats_list.append(stats)
    
    stats_df = pd.DataFrame(stats_list)
    stats_df = stats_df.sort_values('num_users', ascending=False)
    stats_df.to_csv(output_file, index=False)
    
    return stats_df

def generate_summary_report(df, output_file):
    """Generate an overall summary report."""
    df['total_volume'] = df['total_buy'] + df['total_sell']
    
    summary = {
        'metric': [],
        'value': []
    }
    
    # Overall statistics
    summary['metric'].extend([
        'Total Users',
        'Total Buy Amount',
        'Total Sell Amount',
        'Total Volume',
        'Total Net Amount',
        'Total Trades',
        'Average Buy per User',
        'Average Sell per User',
        'Average Volume per User',
        'Average Net per User',
        'Average Trades per User',
        'Average Markets per User',
        'Median Buy per User',
        'Median Sell per User',
        'Median Volume per User',
        'Median Net per User',
        'Median Trades per User',
        'Median Markets per User',
    ])
    
    summary['value'].extend([
        len(df),
        df['total_buy'].sum(),
        df['total_sell'].sum(),
        df['total_volume'].sum(),
        df['net_amount'].sum(),
        df['num_trades'].sum(),
        df['total_buy'].mean(),
        df['total_sell'].mean(),
        df['total_volume'].mean(),
        df['net_amount'].mean(),
        df['num_trades'].mean(),
        df['num_markets'].mean(),
        df['total_buy'].median(),
        df['total_sell'].median(),
        df['total_volume'].median(),
        df['net_amount'].median(),
        df['num_trades'].median(),
        df['num_markets'].median(),
    ])
    
    # Percentiles
    for metric in ['total_buy', 'total_sell', 'net_amount', 'num_trades', 'num_markets', 'total_volume']:
        percentiles = calculate_percentiles(df, metric)
        for p_name, p_value in percentiles.items():
            summary['metric'].append(f'{metric}_{p_name}')
            summary['value'].append(p_value)
    
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(output_file, index=False)
    
    return summary_df

def main():
    """Main execution function."""
    print("=" * 60)
    print("User Segmentation Analysis")
    print("=" * 60)
    
    # Load data
    print(f"\nLoading data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} users")
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Apply segmentation
    print("\nApplying segmentation (Small, Medium, Large)...")
    df = segment_users(df)
    
    # Save segmented data
    segmented_file = OUTPUT_DIR / "user_segments.csv"
    df.to_csv(segmented_file, index=False)
    print(f"Saved segmented data to {segmented_file}")
    
    # Generate statistics for the three segments
    print("\nGenerating segment statistics...")
    output_file = OUTPUT_DIR / "segment_statistics.csv"
    stats_df = generate_segment_stats(df, 'segment', output_file)
    print(f"  Saved: {output_file} ({len(stats_df)} segments)")
    
    # Generate overall summary
    print("\nGenerating overall summary...")
    summary_file = OUTPUT_DIR / "overall_summary.csv"
    summary_df = generate_summary_report(df, summary_file)
    print(f"  Saved: {summary_file}")
    
    # Print key insights
    print("\n" + "=" * 60)
    print("Key Insights")
    print("=" * 60)
    
    print(f"\nTotal Users: {len(df):,}")
    print(f"Total Trading Volume: ${df['total_volume'].sum():,.2f}")
    print(f"Average Volume per User: ${df['total_volume'].mean():,.2f}")
    print(f"Median Volume per User: ${df['total_volume'].median():,.2f}")
    
    print("\nSegment Distribution:")
    segment_stats = df.groupby('segment').size().sort_values(ascending=False)
    for segment, count in segment_stats.items():
        pct = (count / len(df)) * 100
        avg_vol = df[df['segment'] == segment]['total_volume'].mean()
        print(f"  {segment}: {count:,} users ({pct:.1f}%) - Avg Volume: ${avg_vol:,.2f}")
    
    print("\n" + "=" * 60)
    print("Analysis complete!")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()

