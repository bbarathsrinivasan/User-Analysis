"""
Helper functions for trade data pipeline processing.
"""
import pandas as pd
from pathlib import Path


def load_market_trades(event_id, market_slug, base_path="raw"):
    """
    Load trade CSV file for a specific market.
    
    Args:
        event_id: Event identifier
        market_slug: Market slug (used to identify the CSV file)
        base_path: Base path to raw data directory (default: "raw")
    
    Returns:
        DataFrame with columns: unix_timestamp, user_id, event_id, market_id, 
        market_slug, token_type, side, quantity
    """
    trades_dir = Path(base_path) / str(event_id) / "trades"
    
    if not trades_dir.exists():
        raise FileNotFoundError(f"Trades directory not found: {trades_dir}")
    
    # Find the CSV file matching the market_slug
    csv_file = trades_dir / f"{market_slug}_trades.csv"
    
    if not csv_file.exists():
        raise FileNotFoundError(f"Trade CSV file not found: {csv_file}")
    
    # Read the CSV file with low_memory=False to avoid dtype warnings
    df = pd.read_csv(csv_file, low_memory=False)
    
    # Map columns from actual CSV structure to expected format
    # Actual columns: proxyWallet, side, size, timestamp, slug, eventSlug, outcome
    # Expected columns: user_id, side, quantity, unix_timestamp, market_slug, event_id, token_type
    
    # Create a new DataFrame with mapped columns
    mapped_df = pd.DataFrame()
    mapped_df['unix_timestamp'] = df['timestamp'].astype(int)
    mapped_df['user_id'] = df['proxyWallet']
    mapped_df['event_id'] = df['eventSlug']
    mapped_df['market_slug'] = df['slug']
    # Use slug as market_id (or we could hash it, but slug should be unique)
    mapped_df['market_id'] = df['slug']
    # Map outcome (Yes/No) to token_type
    mapped_df['token_type'] = df['outcome'].str.upper()
    mapped_df['side'] = df['side']
    mapped_df['quantity'] = pd.to_numeric(df['size'], errors='coerce')
    
    # Drop any rows with NaN quantity (invalid data)
    mapped_df = mapped_df.dropna(subset=['quantity'])
    
    return mapped_df


def convert_to_utc_date(df):
    """
    Convert unix_timestamp to UTC date.
    
    Args:
        df: DataFrame with unix_timestamp column
    
    Returns:
        DataFrame with new 'date' column (UTC date)
    """
    df = df.copy()
    # Convert unix timestamp to UTC datetime, then extract date
    df['date'] = pd.to_datetime(df['unix_timestamp'], unit='s', utc=True).dt.date
    return df


def compute_day_offset(df):
    """
    Compute day_offset such that the last trading day is 0, 
    and previous days are -1, -2, etc.
    
    Args:
        df: DataFrame with 'date' column
    
    Returns:
        DataFrame with 'day_offset' column
    """
    df = df.copy()
    
    # Find the maximum date (last trading day)
    max_date = df['date'].max()
    
    # Convert dates to datetime for calculation, then compute day offset
    # last day = 0, previous days are negative
    df['day_offset'] = (pd.to_datetime(df['date']) - pd.to_datetime(max_date)).dt.days
    
    return df


def aggregate_daily_trades(df, event_id, market_id, market_slug):
    """
    Aggregate daily buy/sell trades per user and token type.
    
    Args:
        df: DataFrame with columns: user_id, token_type, day_offset, side, quantity
        event_id: Event identifier
        market_id: Market identifier
        market_slug: Market slug
    
    Returns:
        DataFrame with columns: event_id, market_id, market_slug, user_id, 
        token_type, day_offset, daily_buy, daily_sell, net_tokens
    """
    # Create separate DataFrames for BUY and SELL
    buy_df = df[df['side'] == 'BUY'].copy()
    sell_df = df[df['side'] == 'SELL'].copy()
    
    # Group by user_id, token_type, and day_offset, then sum quantities
    daily_buy = buy_df.groupby(['user_id', 'token_type', 'day_offset'])['quantity'].sum().reset_index(name='daily_buy')
    daily_sell = sell_df.groupby(['user_id', 'token_type', 'day_offset'])['quantity'].sum().reset_index(name='daily_sell')
    
    # Get all unique combinations of user_id, token_type, day_offset
    all_combinations = df[['user_id', 'token_type', 'day_offset']].drop_duplicates()
    
    # Merge buy and sell data
    result = all_combinations.merge(daily_buy, on=['user_id', 'token_type', 'day_offset'], how='left')
    result = result.merge(daily_sell, on=['user_id', 'token_type', 'day_offset'], how='left')
    
    # Fill NaN values with 0
    result['daily_buy'] = result['daily_buy'].fillna(0)
    result['daily_sell'] = result['daily_sell'].fillna(0)
    
    # Compute net_tokens
    result['net_tokens'] = result['daily_buy'] - result['daily_sell']
    
    # Add event_id, market_id, market_slug
    result['event_id'] = event_id
    result['market_id'] = market_id
    result['market_slug'] = market_slug
    
    # Reorder columns
    result = result[['event_id', 'market_id', 'market_slug', 'user_id', 
                     'token_type', 'day_offset', 'daily_buy', 'daily_sell', 'net_tokens']]
    
    return result


def fill_missing_days_and_compute_cumulative(df):
    """
    Fill missing days with zeros and compute cumulative position.
    
    For each (user_id, token_type) combination:
    - Creates complete day range from min(day_offset) to 0
    - Fills missing days with daily_buy=0, daily_sell=0
    - Computes cumulative_position as running sum of net_tokens
    
    Args:
        df: DataFrame with columns: event_id, market_id, market_slug, user_id,
            token_type, day_offset, daily_buy, daily_sell, net_tokens
    
    Returns:
        DataFrame with cumulative_position column added
    """
    result_dfs = []
    
    # Group by user_id and token_type
    for (user_id, token_type), group_df in df.groupby(['user_id', 'token_type']):
        # Get the day range for this user/token combination
        min_day = int(group_df['day_offset'].min())
        max_day = 0  # Last trading day is always 0
        
        # Create complete day range
        complete_days = pd.RangeIndex(start=min_day, stop=max_day + 1, step=1)
        
        # Set day_offset as index for reindexing
        group_df = group_df.set_index('day_offset')
        
        # Reindex to include all days
        group_df = group_df.reindex(complete_days)
        
        # Fill missing days with zeros for daily_buy and daily_sell
        group_df['daily_buy'] = group_df['daily_buy'].fillna(0)
        group_df['daily_sell'] = group_df['daily_sell'].fillna(0)
        
        # Fill metadata columns - these should be constant for each (user_id, token_type) group
        # Use the first non-null value (should exist from original data)
        for col in ['event_id', 'market_id', 'market_slug', 'user_id', 'token_type']:
            if col in group_df.columns:
                # Get first non-null value and fill all rows
                first_value = group_df[col].dropna().iloc[0] if not group_df[col].dropna().empty else None
                if first_value is not None:
                    group_df[col] = group_df[col].fillna(first_value)
                else:
                    # Fallback: use ffill and bfill if no non-null values exist
                    group_df[col] = group_df[col].ffill().bfill()
        
        # Recalculate net_tokens for all days (including newly filled days)
        group_df['net_tokens'] = group_df['daily_buy'] - group_df['daily_sell']
        
        # Sort by day_offset (ascending: most negative to 0)
        group_df = group_df.sort_index()
        
        # Compute cumulative_position as running sum of net_tokens
        group_df['cumulative_position'] = group_df['net_tokens'].cumsum()
        
        # Reset index to make day_offset a column again
        group_df = group_df.reset_index()
        # Rename the index column back to day_offset
        group_df = group_df.rename(columns={'index': 'day_offset'})
        
        result_dfs.append(group_df)
    
    # Concatenate all results
    result = pd.concat(result_dfs, ignore_index=True)
    
    return result


def write_user_output(df, user_id, event_id, market_id, token_type, base_path="output"):
    """
    Write user output CSV file for a specific token type.
    
    Args:
        df: DataFrame with all required columns
        user_id: User identifier
        event_id: Event identifier
        market_id: Market identifier
        token_type: Token type ('YES' or 'NO')
        base_path: Base path for output directory (default: "output")
    """
    # Create output directory
    output_dir = Path(base_path) / f"user_{user_id}" / f"event_{event_id}" / f"market_{market_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter for specific user and token type
    filtered_df = df[(df['user_id'] == user_id) & (df['token_type'] == token_type)].copy()
    
    # Select columns in the required order
    output_columns = ['event_id', 'market_id', 'market_slug', 'user_id', 
                     'day_offset', 'daily_buy', 'daily_sell', 'net_tokens', 'cumulative_position']
    
    output_df = filtered_df[output_columns].copy()
    
    # Sort by day_offset (ascending)
    output_df = output_df.sort_values('day_offset')
    
    # Determine output filename
    filename = "yes_token.csv" if token_type == "YES" else "no_token.csv"
    output_path = output_dir / filename
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)


def aggregate_all_markets_trades(all_markets_df):
    """
    Aggregate daily trades across all markets, preserving event_id and market_id.
    
    Args:
        all_markets_df: DataFrame with columns from all markets: event_id, market_id, 
                       market_slug, user_id, token_type, day_offset, daily_buy, 
                       daily_sell, net_tokens
    
    Returns:
        DataFrame with aggregated daily_buy and daily_sell per (user_id, token_type, 
        event_id, market_id, day_offset) combination
    """
    # Group by user_id, token_type, event_id, market_id, and day_offset
    # Sum daily_buy and daily_sell
    aggregated = all_markets_df.groupby(
        ['user_id', 'token_type', 'event_id', 'market_id', 'day_offset']
    ).agg({
        'market_slug': 'first',  # Take first value (should be same for each market_id)
        'daily_buy': 'sum',
        'daily_sell': 'sum'
    }).reset_index()
    
    # Recompute net_tokens after aggregation
    aggregated['net_tokens'] = aggregated['daily_buy'] - aggregated['daily_sell']
    
    # Reorder columns
    aggregated = aggregated[['event_id', 'market_id', 'market_slug', 'user_id', 
                              'token_type', 'day_offset', 'daily_buy', 'daily_sell', 'net_tokens']]
    
    return aggregated


def compute_global_cumulative_position(df):
    """
    Compute global cumulative_position across all markets for each user/token_type.
    Sorted by day_offset first (chronological), then by event_id and market_id.
    
    Args:
        df: DataFrame with columns: event_id, market_id, market_slug, user_id,
            token_type, day_offset, daily_buy, daily_sell, net_tokens
    
    Returns:
        DataFrame with cumulative_position column added (global across all markets)
    """
    result_dfs = []
    
    # Group by user_id and token_type
    for (user_id, token_type), group_df in df.groupby(['user_id', 'token_type']):
        # Sort by day_offset first (chronological), then event_id, market_id
        # This ensures cumulative position is based on date progression across markets
        group_df = group_df.sort_values(['day_offset', 'event_id', 'market_id']).copy()
        
        # Compute cumulative_position as running sum of net_tokens
        group_df['cumulative_position'] = group_df['net_tokens'].cumsum()
        
        result_dfs.append(group_df)
    
    # Concatenate all results
    result = pd.concat(result_dfs, ignore_index=True)
    
    return result


def write_all_markets_user_output(df, user_id, token_type, base_path="all_markets_output"):
    """
    Write aggregated output files for a user across all markets.
    
    Args:
        df: DataFrame with all required columns (all markets combined)
        user_id: User identifier
        token_type: Token type ('YES' or 'NO')
        base_path: Base path for output directory (default: "all_markets_output")
    """
    # Create output directory
    output_dir = Path(base_path) / f"user_{user_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter for specific user and token type
    filtered_df = df[(df['user_id'] == user_id) & (df['token_type'] == token_type)].copy()
    
    if filtered_df.empty:
        return
    
    # Select columns in the required order
    output_columns = ['event_id', 'market_id', 'market_slug', 'user_id', 
                     'day_offset', 'daily_buy', 'daily_sell', 'net_tokens', 'cumulative_position']
    
    output_df = filtered_df[output_columns].copy()
    
    # Sort by day_offset first (chronological), then event_id, market_id
    # This ensures all markets' trades for the same day are grouped together
    output_df = output_df.sort_values(['day_offset', 'event_id', 'market_id'])
    
    # Determine output filename
    filename = "yes_token.csv" if token_type == "YES" else "no_token.csv"
    output_path = output_dir / filename
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)
