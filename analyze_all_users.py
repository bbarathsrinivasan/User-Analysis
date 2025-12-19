"""
Script to analyze all users based on date_group_token.csv files.
Calculates statistics for each user to understand their trading behavior.
"""
import pandas as pd
from pathlib import Path
import numpy as np


def calculate_user_statistics(user_id, base_path="all_markets_output"):
    """
    Calculate statistics for a single user based on their date_group_token.csv file.
    
    Args:
        user_id: User identifier
        base_path: Base path for output directory (default: "all_markets_output")
    
    Returns:
        Dictionary with user statistics or None if file doesn't exist
    """
    user_dir = Path(base_path) / f"user_{user_id}"
    date_group_file = user_dir / "date_group_token.csv"
    
    if not date_group_file.exists():
        return None
    
    try:
        df = pd.read_csv(date_group_file, low_memory=False)
        
        if df.empty:
            return None
        
        # Ensure date is datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Calculate statistics
        stats = {
            'user_id': user_id,
            'total_days': len(df),
            'first_date': df['date'].min().strftime('%Y-%m-%d'),
            'last_date': df['date'].max().strftime('%Y-%m-%d'),
            'date_range_days': (df['date'].max() - df['date'].min()).days,
        }
        
        # Total Token Statistics
        stats['total_token_min'] = df['total_token'].min()
        stats['total_token_max'] = df['total_token'].max()
        stats['total_token_mean'] = df['total_token'].mean()
        stats['total_token_median'] = df['total_token'].median()
        stats['total_token_sum'] = df['total_token'].sum()
        
        # Total Value Statistics
        stats['total_value_min'] = df['total_value'].min()
        stats['total_value_max'] = df['total_value'].max()
        stats['total_value_mean'] = df['total_value'].mean()
        stats['total_value_median'] = df['total_value'].median()
        stats['total_value_sum'] = df['total_value'].sum()
        
        # Cumulative Total Token Statistics
        stats['cumulative_total_token_final'] = df['cumulative_total_token'].iloc[-1] if len(df) > 0 else 0
        stats['cumulative_total_token_max'] = df['cumulative_total_token'].max()
        stats['cumulative_total_token_min'] = df['cumulative_total_token'].min()
        
        # Cumulative Total Value Statistics
        stats['cumulative_total_value_final'] = df['cumulative_total_value'].iloc[-1] if len(df) > 0 else 0
        stats['cumulative_total_value_max'] = df['cumulative_total_value'].max()
        stats['cumulative_total_value_min'] = df['cumulative_total_value'].min()
        
        # Net YES Statistics
        stats['net_yes_min'] = df['net_yes'].min()
        stats['net_yes_max'] = df['net_yes'].max()
        stats['net_yes_mean'] = df['net_yes'].mean()
        stats['net_yes_sum'] = df['net_yes'].sum()
        stats['net_yes_final_cumulative'] = df['cumulative_net_yes'].iloc[-1] if len(df) > 0 else 0
        
        # Net NO Statistics
        stats['net_no_min'] = df['net_no'].min()
        stats['net_no_max'] = df['net_no'].max()
        stats['net_no_mean'] = df['net_no'].mean()
        stats['net_no_sum'] = df['net_no'].sum()
        stats['net_no_final_cumulative'] = df['cumulative_net_no'].iloc[-1] if len(df) > 0 else 0
        
        # YES Value Statistics
        stats['yes_value_min'] = df['yes_value'].min()
        stats['yes_value_max'] = df['yes_value'].max()
        stats['yes_value_mean'] = df['yes_value'].mean()
        stats['yes_value_sum'] = df['yes_value'].sum()
        stats['yes_value_final_cumulative'] = df['cumulative_yes_value'].iloc[-1] if len(df) > 0 else 0
        
        # NO Value Statistics
        stats['no_value_min'] = df['no_value'].min()
        stats['no_value_max'] = df['no_value'].max()
        stats['no_value_mean'] = df['no_value'].mean()
        stats['no_value_sum'] = df['no_value'].sum()
        stats['no_value_final_cumulative'] = df['cumulative_no_value'].iloc[-1] if len(df) > 0 else 0
        
        # Trading Activity Statistics
        stats['total_markets_engaged'] = df['markets_engaged'].sum()
        
        return stats
        
    except Exception as e:
        print(f"  Error processing user {user_id}: {str(e)}")
        return None


def analyze_all_users(base_path="all_markets_output", output_file="all_users_analysis.csv"):
    """
    Analyze all users and create a summary CSV file.
    
    Args:
        base_path: Base path for output directory (default: "all_markets_output")
        output_file: Output CSV file name (default: "all_users_analysis.csv")
    """
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"Error: Directory not found at {base_path}")
        return
    
    # Find all user directories
    user_dirs = [d for d in base_path.iterdir() if d.is_dir() and d.name.startswith('user_')]
    
    if not user_dirs:
        print(f"Warning: No user directories found in {base_path}")
        return
    
    print(f"Found {len(user_dirs)} users to analyze...")
    
    all_stats = []
    processed = 0
    errors = 0
    
    for user_dir in user_dirs:
        user_id = user_dir.name.replace('user_', '')
        stats = calculate_user_statistics(user_id, base_path)
        
        if stats:
            all_stats.append(stats)
            processed += 1
        else:
            errors += 1
        
        if processed % 500 == 0:
            print(f"  Processed {processed} users...")
    
    if not all_stats:
        print("No user statistics to save")
        return
    
    # Create DataFrame and save
    df = pd.DataFrame(all_stats)
    
    # Reorder columns for better readability
    column_order = [
        'user_id', 'total_days', 'first_date', 'last_date', 'date_range_days',
        'total_markets_engaged',
        'total_token_min', 'total_token_max', 'total_token_mean', 'total_token_median', 
        'total_token_sum',
        'total_value_min', 'total_value_max', 'total_value_mean', 'total_value_median',
        'total_value_sum',
        'cumulative_total_token_final', 'cumulative_total_token_max', 'cumulative_total_token_min',
        'cumulative_total_value_final', 'cumulative_total_value_max', 'cumulative_total_value_min',
        'net_yes_min', 'net_yes_max', 'net_yes_mean', 'net_yes_sum', 'net_yes_final_cumulative',
        'net_no_min', 'net_no_max', 'net_no_mean', 'net_no_sum', 'net_no_final_cumulative',
        'yes_value_min', 'yes_value_max', 'yes_value_mean', 'yes_value_sum', 'yes_value_final_cumulative',
        'no_value_min', 'no_value_max', 'no_value_mean', 'no_value_sum', 'no_value_final_cumulative'
    ]
    
    # Only include columns that exist
    available_columns = [col for col in column_order if col in df.columns]
    df = df[available_columns]
    
    # Save to CSV
    output_path = Path(output_file)
    df.to_csv(output_path, index=False)
    
    print(f"\nAnalysis completed!")
    print(f"  Processed: {processed} users")
    print(f"  Errors: {errors} users")
    print(f"  Output saved to: {output_path}")
    print(f"  Total statistics: {len(df.columns)} columns")


if __name__ == "__main__":
    analyze_all_users()
