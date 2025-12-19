"""
Helper functions for trade data pipeline processing.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime


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


def load_market_prices(event_id, market_slug, base_path="raw"):
    """
    Load price CSV file for a specific market and create a mapping of token_id to token_type (YES/NO).
    Also returns end-of-day prices for each date.
    
    Args:
        event_id: Event identifier
        market_slug: Market slug (used to identify the CSV file)
        base_path: Base path to raw data directory (default: "raw")
    
    Returns:
        tuple: (token_id_to_type_dict, prices_df)
            - token_id_to_type_dict: Dictionary mapping token_id to 'YES' or 'NO'
            - prices_df: DataFrame with columns: date, yes_token_price, no_token_price
    """
    prices_dir = Path(base_path) / str(event_id) / "prices"
    
    if not prices_dir.exists():
        return None, None
    
    # Find the price CSV file matching the market_slug
    price_file = prices_dir / f"{market_slug}_price.csv"
    
    if not price_file.exists():
        return None, None
    
    # Load trades to get token_id to outcome mapping
    trades_dir = Path(base_path) / str(event_id) / "trades"
    trades_file = trades_dir / f"{market_slug}_trades.csv"
    
    token_id_to_type = {}
    
    if trades_file.exists():
        try:
            trades_df = pd.read_csv(trades_file, low_memory=False)
            if 'asset' in trades_df.columns and 'outcome' in trades_df.columns:
                # Create mapping: token_id (asset) -> token_type (YES/NO)
                for _, row in trades_df[['asset', 'outcome']].drop_duplicates().iterrows():
                    token_id = str(row['asset'])
                    outcome = str(row['outcome']).upper()
                    if outcome in ['YES', 'NO']:
                        token_id_to_type[token_id] = outcome
        except Exception:
            pass
    
    # Load price data
    try:
        prices_df = pd.read_csv(price_file, low_memory=False)
    except Exception:
        return None, None
    
    if prices_df.empty or 'token_id' not in prices_df.columns:
        return None, None
    
    # Convert timestamp to datetime and date
    prices_df['timestamp'] = pd.to_numeric(prices_df['timestamp'], errors='coerce')
    prices_df = prices_df.dropna(subset=['timestamp'])
    
    if prices_df.empty:
        return None, None
    
    prices_df['datetime'] = pd.to_datetime(prices_df['timestamp'], unit='s', utc=True)
    prices_df['date'] = prices_df['datetime'].dt.date
    
    # If we don't have token_id mapping from trades, we'll need to infer it
    # For now, we'll use the first token_id as YES and second as NO if not mapped
    unique_token_ids = prices_df['token_id'].unique()
    if not token_id_to_type and len(unique_token_ids) == 2:
        # Default: first token_id is YES, second is NO
        token_id_to_type[str(unique_token_ids[0])] = 'YES'
        token_id_to_type[str(unique_token_ids[1])] = 'NO'
    
    # Map token_id to token_type
    prices_df['token_type'] = prices_df['token_id'].astype(str).map(token_id_to_type)
    
    # Filter out rows where token_type couldn't be determined
    prices_df = prices_df[prices_df['token_type'].notna()]
    
    if prices_df.empty:
        return None, None
    
    # Get end-of-day prices (last price for each date and token_type)
    end_of_day_prices = prices_df.sort_values('timestamp').groupby(['date', 'token_type']).last().reset_index()
    
    # Pivot to have yes_token_price and no_token_price columns
    price_pivot = end_of_day_prices.pivot_table(
        index='date',
        columns='token_type',
        values='price',
        aggfunc='last'
    ).reset_index()
    
    # Rename columns
    result_df = pd.DataFrame()
    result_df['date'] = price_pivot['date']
    
    if 'YES' in price_pivot.columns:
        result_df['yes_token_price'] = price_pivot['YES']
    else:
        result_df['yes_token_price'] = None
    
    if 'NO' in price_pivot.columns:
        result_df['no_token_price'] = price_pivot['NO']
    else:
        result_df['no_token_price'] = None
    
    # Forward-fill missing prices (carry forward last known price)
    result_df['yes_token_price'] = result_df['yes_token_price'].ffill()
    result_df['no_token_price'] = result_df['no_token_price'].ffill()
    
    return token_id_to_type, result_df


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
        df: DataFrame with columns: user_id, token_type, day_offset, side, quantity, date
        event_id: Event identifier
        market_id: Market identifier
        market_slug: Market slug
    
    Returns:
        DataFrame with columns: event_id, market_id, market_slug, user_id, 
        token_type, day_offset, date, daily_buy, daily_sell, net_tokens
    """
    # Create separate DataFrames for BUY and SELL
    buy_df = df[df['side'] == 'BUY'].copy()
    sell_df = df[df['side'] == 'SELL'].copy()
    
    # Group by user_id, token_type, and day_offset, then sum quantities
    daily_buy = buy_df.groupby(['user_id', 'token_type', 'day_offset'])['quantity'].sum().reset_index(name='daily_buy')
    daily_sell = sell_df.groupby(['user_id', 'token_type', 'day_offset'])['quantity'].sum().reset_index(name='daily_sell')
    
    # Get date for each day_offset (take first date for each day_offset - should be same for all rows with same day_offset)
    date_mapping = df.groupby('day_offset')['date'].first().reset_index()
    date_mapping.columns = ['day_offset', 'date']
    
    # Get all unique combinations of user_id, token_type, day_offset
    all_combinations = df[['user_id', 'token_type', 'day_offset']].drop_duplicates()
    
    # Merge buy and sell data
    result = all_combinations.merge(daily_buy, on=['user_id', 'token_type', 'day_offset'], how='left')
    result = result.merge(daily_sell, on=['user_id', 'token_type', 'day_offset'], how='left')
    result = result.merge(date_mapping, on='day_offset', how='left')
    
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
                     'token_type', 'day_offset', 'date', 'daily_buy', 'daily_sell', 'net_tokens']]
    
    return result


def fill_missing_days_and_compute_cumulative(df):
    """
    Fill missing days with zeros and compute cumulative position.
    
    For each (user_id, token_type) combination:
    - Creates complete day range from min(day_offset) to 0
    - Fills missing days with daily_buy=0, daily_sell=0
    - Computes cumulative_position as running sum of net_tokens
    - Computes date and timestamp for each day_offset
    
    Args:
        df: DataFrame with columns: event_id, market_id, market_slug, user_id,
            token_type, day_offset, date, daily_buy, daily_sell, net_tokens
    
    Returns:
        DataFrame with cumulative_position, date, and timestamp columns added
    """
    result_dfs = []
    
    # Group by user_id and token_type
    for (user_id, token_type), group_df in df.groupby(['user_id', 'token_type']):
        # Get the day range for this user/token combination
        min_day = int(group_df['day_offset'].min())
        max_day = 0  # Last trading day is always 0
        
        # Get the last trading day (day_offset = 0) date to compute dates for missing days
        last_trading_date_row = group_df[group_df['day_offset'] == 0]
        last_trading_date = last_trading_date_row['date'].iloc[0] if len(last_trading_date_row) > 0 else None
        
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
        
        # Compute dates for all day_offsets based on the last trading date
        if last_trading_date is not None:
            # Convert last_trading_date to datetime if it's a date object
            if isinstance(last_trading_date, pd.Timestamp):
                last_trading_datetime = last_trading_date
            elif isinstance(last_trading_date, pd._libs.tslibs.timestamps.Timestamp):
                last_trading_datetime = last_trading_date
            else:
                last_trading_datetime = pd.to_datetime(last_trading_date)
            
            # Compute dates for ALL day_offsets (recompute to ensure consistency)
            for day_offset in group_df.index:
                computed_date = last_trading_datetime + pd.Timedelta(days=int(day_offset))
                # Ensure we store as date object
                if isinstance(computed_date, pd.Timestamp):
                    group_df.loc[day_offset, 'date'] = computed_date.date()
                else:
                    group_df.loc[day_offset, 'date'] = computed_date
        else:
            # Fallback: if no last trading date, try to use existing dates or compute from any available date
            # Find any non-null date to use as reference
            existing_dates = group_df['date'].dropna()
            if not existing_dates.empty:
                # Use the date from day_offset=0 if available, otherwise use the first available
                ref_date_row = group_df[group_df['date'].notna()]
                if len(ref_date_row) > 0:
                    ref_date = ref_date_row['date'].iloc[0]
                    ref_day_offset = ref_date_row.index[0]
                    if isinstance(ref_date, pd.Timestamp):
                        ref_datetime = ref_date
                    else:
                        ref_datetime = pd.to_datetime(ref_date)
                    
                    # Compute all dates relative to this reference
                    for day_offset in group_df.index:
                        days_diff = int(day_offset) - int(ref_day_offset)
                        computed_date = ref_datetime + pd.Timedelta(days=days_diff)
                        if isinstance(computed_date, pd.Timestamp):
                            group_df.loc[day_offset, 'date'] = computed_date.date()
                        else:
                            group_df.loc[day_offset, 'date'] = computed_date
        
        # Compute timestamp from date (start of day in UTC)
        # Convert date to datetime at start of day in UTC, then to unix timestamp
        group_df['timestamp'] = pd.to_datetime(group_df['date'], utc=True).astype('int64') // 10**9
        
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
    
    # Filter out rows where both daily_buy and daily_sell are 0 (no trades)
    filtered_df = filtered_df[~((filtered_df['daily_buy'] == 0) & (filtered_df['daily_sell'] == 0))].copy()
    
    if filtered_df.empty:
        return
    
    # Select columns in the required order
    output_columns = ['event_id', 'market_id', 'market_slug', 'user_id', 
                     'day_offset', 'timestamp', 'date', 'daily_buy', 'daily_sell', 'net_tokens', 'cumulative_position']
    
    output_df = filtered_df[output_columns].copy()
    
    # Sort by day_offset (ascending)
    output_df = output_df.sort_values('day_offset')
    
    # Determine output filename
    filename = "yes_token.csv" if token_type == "YES" else "no_token.csv"
    output_path = output_dir / filename
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)


def write_combined_token_output(df, user_id, event_id, market_id, base_path="output"):
    """
    Write combined token CSV file for a user in a specific market, merging YES and NO token data.
    
    Args:
        df: DataFrame with all required columns for both YES and NO tokens
        user_id: User identifier
        event_id: Event identifier
        market_id: Market identifier
        base_path: Base path for output directory (default: "output")
    """
    # Create output directory
    output_dir = Path(base_path) / f"user_{user_id}" / f"event_{event_id}" / f"market_{market_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter for specific user
    user_df = df[df['user_id'] == user_id].copy()
    
    if user_df.empty:
        return
    
    # Separate YES and NO token data
    yes_df = user_df[user_df['token_type'] == 'YES'].copy()
    no_df = user_df[user_df['token_type'] == 'NO'].copy()
    
    # Filter out rows where both daily_buy and daily_sell are 0 (no trades)
    yes_df = yes_df[~((yes_df['daily_buy'] == 0) & (yes_df['daily_sell'] == 0))].copy()
    no_df = no_df[~((no_df['daily_buy'] == 0) & (no_df['daily_sell'] == 0))].copy()
    
    # Get all unique day_offsets from both YES and NO data
    all_day_offsets = set()
    if not yes_df.empty:
        all_day_offsets.update(yes_df['day_offset'].unique())
    if not no_df.empty:
        all_day_offsets.update(no_df['day_offset'].unique())
    
    if not all_day_offsets:
        return
    
    # Create a base DataFrame with all day_offsets
    base_columns = ['event_id', 'market_id', 'market_slug', 'user_id', 'day_offset', 'timestamp', 'date']
    
    # Get metadata from first row (should be same for all rows in same market)
    if not yes_df.empty:
        sample_row = yes_df.iloc[0]
    elif not no_df.empty:
        sample_row = no_df.iloc[0]
    else:
        return
    
    combined_data = []
    for day_offset in sorted(all_day_offsets):
        # Get YES data for this day_offset
        yes_row = yes_df[yes_df['day_offset'] == day_offset]
        # Get NO data for this day_offset
        no_row = no_df[no_df['day_offset'] == day_offset]
        
        # Get timestamp and date (prefer from YES, fallback to NO)
        if not yes_row.empty:
            timestamp = yes_row.iloc[0]['timestamp']
            date = yes_row.iloc[0]['date']
        elif not no_row.empty:
            timestamp = no_row.iloc[0]['timestamp']
            date = no_row.iloc[0]['date']
        else:
            continue
        
        row_data = {
            'event_id': sample_row['event_id'],
            'market_id': sample_row['market_id'],
            'market_slug': sample_row['market_slug'],
            'user_id': user_id,
            'day_offset': day_offset,
            'timestamp': timestamp,
            'date': date,
            'yes_daily_buy': yes_row.iloc[0]['daily_buy'] if not yes_row.empty else 0.0,
            'yes_daily_sell': yes_row.iloc[0]['daily_sell'] if not yes_row.empty else 0.0,
            'yes_net_tokens': yes_row.iloc[0]['net_tokens'] if not yes_row.empty else 0.0,
            'yes_cumulative_position': yes_row.iloc[0]['cumulative_position'] if not yes_row.empty else None,
            'no_daily_buy': no_row.iloc[0]['daily_buy'] if not no_row.empty else 0.0,
            'no_daily_sell': no_row.iloc[0]['daily_sell'] if not no_row.empty else 0.0,
            'no_net_tokens': no_row.iloc[0]['net_tokens'] if not no_row.empty else 0.0,
            'no_cumulative_position': no_row.iloc[0]['cumulative_position'] if not no_row.empty else None,
        }
        combined_data.append(row_data)
    
    combined_df = pd.DataFrame(combined_data)
    
    # Sort by day_offset first
    combined_df = combined_df.sort_values('day_offset')
    
    # Forward-fill cumulative positions (carry forward last known value)
    combined_df['yes_cumulative_position'] = combined_df['yes_cumulative_position'].ffill().fillna(0.0)
    combined_df['no_cumulative_position'] = combined_df['no_cumulative_position'].ffill().fillna(0.0)
    
    # Filter out rows where both YES and NO have no trades
    combined_df = combined_df[~(
        (combined_df['yes_daily_buy'] == 0) & (combined_df['yes_daily_sell'] == 0) &
        (combined_df['no_daily_buy'] == 0) & (combined_df['no_daily_sell'] == 0)
    )].copy()
    
    if combined_df.empty:
        return
    
    # Write to CSV
    output_path = output_dir / "combined_token.csv"
    combined_df.to_csv(output_path, index=False)


def aggregate_all_markets_trades(all_markets_df):
    """
    Aggregate daily trades across all markets, preserving event_id and market_id.
    
    Args:
        all_markets_df: DataFrame with columns from all markets: event_id, market_id, 
                       market_slug, user_id, token_type, day_offset, date, daily_buy, 
                       daily_sell, net_tokens
    
    Returns:
        DataFrame with aggregated daily_buy and daily_sell per (user_id, token_type, 
        event_id, market_id, day_offset) combination, with date preserved
    """
    # Group by user_id, token_type, event_id, market_id, and day_offset
    # Sum daily_buy and daily_sell, take first date (should be same for same day_offset within market)
    aggregated = all_markets_df.groupby(
        ['user_id', 'token_type', 'event_id', 'market_id', 'day_offset']
    ).agg({
        'market_slug': 'first',  # Take first value (should be same for each market_id)
        'date': 'first',  # Take first date (should be same for same day_offset within market)
        'daily_buy': 'sum',
        'daily_sell': 'sum'
    }).reset_index()
    
    # Recompute net_tokens after aggregation
    aggregated['net_tokens'] = aggregated['daily_buy'] - aggregated['daily_sell']
    
    # Compute timestamp from date (start of day in UTC)
    aggregated['timestamp'] = pd.to_datetime(aggregated['date'], utc=True).astype('int64') // 10**9
    
    # Reorder columns
    aggregated = aggregated[['event_id', 'market_id', 'market_slug', 'user_id', 
                              'token_type', 'day_offset', 'timestamp', 'date', 'daily_buy', 'daily_sell', 'net_tokens']]
    
    return aggregated


def compute_global_cumulative_position(df):
    """
    Compute global cumulative_position across all markets and all events for each user/token_type.
    Sorted by day_offset first (chronological), then by market_id (not event_id).
    This ensures all markets from all events with the same day_offset are grouped together.
    
    Args:
        df: DataFrame with columns: event_id, market_id, market_slug, user_id,
            token_type, day_offset, daily_buy, daily_sell, net_tokens
    
    Returns:
        DataFrame with cumulative_position column added (global across all markets and events)
    """
    result_dfs = []
    
    # Group by user_id and token_type
    for (user_id, token_type), group_df in df.groupby(['user_id', 'token_type']):
        # Sort by day_offset first (chronological), then market_id (NOT event_id)
        # This ensures all markets from all events with the same day_offset are grouped together
        # Cumulative position is truly global across all events
        group_df = group_df.sort_values(['day_offset', 'market_id']).copy()
        
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
    
    # Filter out rows where both daily_buy and daily_sell are 0 (no trades)
    filtered_df = filtered_df[~((filtered_df['daily_buy'] == 0) & (filtered_df['daily_sell'] == 0))].copy()
    
    if filtered_df.empty:
        return
    
    # Select columns in the required order
    output_columns = ['event_id', 'market_id', 'market_slug', 'user_id', 
                     'day_offset', 'timestamp', 'date', 'daily_buy', 'daily_sell', 'net_tokens', 'cumulative_position']
    
    output_df = filtered_df[output_columns].copy()
    
    # Sort by day_offset first (chronological), then market_id (NOT event_id)
    # This ensures all markets from all events with the same day_offset are grouped together
    output_df = output_df.sort_values(['day_offset', 'market_id'])
    
    # Determine output filename
    filename = "yes_token.csv" if token_type == "YES" else "no_token.csv"
    output_path = output_dir / filename
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)


def write_all_markets_combined_token_output(df, user_id, base_path="all_markets_output"):
    """
    Write combined token CSV file for a user across all markets, merging YES and NO token data.
    
    Args:
        df: DataFrame with all required columns (all markets combined, both YES and NO tokens)
        user_id: User identifier
        base_path: Base path for output directory (default: "all_markets_output")
    """
    # Create output directory
    output_dir = Path(base_path) / f"user_{user_id}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter for specific user
    user_df = df[df['user_id'] == user_id].copy()
    
    if user_df.empty:
        return
    
    # Separate YES and NO token data
    yes_df = user_df[user_df['token_type'] == 'YES'].copy()
    no_df = user_df[user_df['token_type'] == 'NO'].copy()
    
    # Filter out rows where both daily_buy and daily_sell are 0 (no trades)
    yes_df = yes_df[~((yes_df['daily_buy'] == 0) & (yes_df['daily_sell'] == 0))].copy()
    no_df = no_df[~((no_df['daily_buy'] == 0) & (no_df['daily_sell'] == 0))].copy()
    
    # Get all unique combinations of (day_offset, market_id) from both YES and NO data
    all_combinations = set()
    if not yes_df.empty:
        all_combinations.update(yes_df[['day_offset', 'market_id']].apply(tuple, axis=1))
    if not no_df.empty:
        all_combinations.update(no_df[['day_offset', 'market_id']].apply(tuple, axis=1))
    
    if not all_combinations:
        return
    
    # Get metadata from first row
    if not yes_df.empty:
        sample_row = yes_df.iloc[0]
    elif not no_df.empty:
        sample_row = no_df.iloc[0]
    else:
        return
    
    combined_data = []
    for day_offset, market_id in sorted(all_combinations):
        # Get YES data for this day_offset and market_id
        yes_row = yes_df[(yes_df['day_offset'] == day_offset) & (yes_df['market_id'] == market_id)]
        # Get NO data for this day_offset and market_id
        no_row = no_df[(no_df['day_offset'] == day_offset) & (no_df['market_id'] == market_id)]
        
        # Get metadata (prefer from YES, fallback to NO)
        if not yes_row.empty:
            row_meta = yes_row.iloc[0]
        elif not no_row.empty:
            row_meta = no_row.iloc[0]
        else:
            continue
        
        row_data = {
            'event_id': row_meta['event_id'],
            'market_id': market_id,
            'market_slug': row_meta['market_slug'],
            'user_id': user_id,
            'day_offset': day_offset,
            'timestamp': row_meta['timestamp'],
            'date': row_meta['date'],
            'yes_daily_buy': yes_row.iloc[0]['daily_buy'] if not yes_row.empty else 0.0,
            'yes_daily_sell': yes_row.iloc[0]['daily_sell'] if not yes_row.empty else 0.0,
            'yes_net_tokens': yes_row.iloc[0]['net_tokens'] if not yes_row.empty else 0.0,
            'yes_cumulative_position': yes_row.iloc[0]['cumulative_position'] if not yes_row.empty else None,
            'no_daily_buy': no_row.iloc[0]['daily_buy'] if not no_row.empty else 0.0,
            'no_daily_sell': no_row.iloc[0]['daily_sell'] if not no_row.empty else 0.0,
            'no_net_tokens': no_row.iloc[0]['net_tokens'] if not no_row.empty else 0.0,
            'no_cumulative_position': no_row.iloc[0]['cumulative_position'] if not no_row.empty else None,
        }
        combined_data.append(row_data)
    
    combined_df = pd.DataFrame(combined_data)
    
    # Sort by day_offset first (chronological), then market_id
    combined_df = combined_df.sort_values(['day_offset', 'market_id'])
    
    # Forward-fill cumulative positions (carry forward last known value globally)
    combined_df['yes_cumulative_position'] = combined_df['yes_cumulative_position'].ffill().fillna(0.0)
    combined_df['no_cumulative_position'] = combined_df['no_cumulative_position'].ffill().fillna(0.0)
    
    # Filter out rows where both YES and NO have no trades
    combined_df = combined_df[~(
        (combined_df['yes_daily_buy'] == 0) & (combined_df['yes_daily_sell'] == 0) &
        (combined_df['no_daily_buy'] == 0) & (combined_df['no_daily_sell'] == 0)
    )].copy()
    
    if combined_df.empty:
        return
    
    # Write to CSV
    output_path = output_dir / "combined_token.csv"
    combined_df.to_csv(output_path, index=False)


def write_date_group_token_output(user_id, base_path="all_markets_output"):
    """
    Create date_group_token.csv for a user by grouping combined_token.csv data by date.
    
    Args:
        user_id: User identifier
        base_path: Base path for output directory (default: "all_markets_output")
    """
    # Read the combined_token.csv file for this user
    user_dir = Path(base_path) / f"user_{user_id}"
    combined_token_file = user_dir / "combined_token.csv"
    
    if not combined_token_file.exists():
        return
    
    try:
        # Read combined token data
        combined_df = pd.read_csv(combined_token_file, low_memory=False)
        
        if combined_df.empty:
            return
        
        # Ensure date is in the correct format
        combined_df['date'] = pd.to_datetime(combined_df['date']).dt.date
        
        # Load closing prices for all unique markets
        unique_markets = combined_df[['event_id', 'market_slug']].drop_duplicates()
        all_closing_prices = []
        
        for _, market_row in unique_markets.iterrows():
            event_id = market_row['event_id']
            market_slug = market_row['market_slug']
            
            # Load closing prices file
            closing_prices_file = Path("raw") / event_id / "prices" / f"{market_slug}_closing_prices.csv"
            
            if closing_prices_file.exists():
                try:
                    closing_df = pd.read_csv(closing_prices_file, low_memory=False)
                    closing_df['date'] = pd.to_datetime(closing_df['date']).dt.date
                    closing_df['event_id'] = event_id
                    closing_df['market_slug'] = market_slug
                    
                    # Pivot to have yes_closing_price and no_closing_price columns
                    closing_pivot = closing_df.pivot_table(
                        index=['event_id', 'market_slug', 'date'],
                        columns='token_type',
                        values='closing_price',
                        aggfunc='first'
                    ).reset_index()
                    
                    # Rename columns
                    if 'YES' in closing_pivot.columns:
                        closing_pivot = closing_pivot.rename(columns={'YES': 'yes_closing_price'})
                    else:
                        closing_pivot['yes_closing_price'] = None
                    
                    if 'NO' in closing_pivot.columns:
                        closing_pivot = closing_pivot.rename(columns={'NO': 'no_closing_price'})
                    else:
                        closing_pivot['no_closing_price'] = None
                    
                    all_closing_prices.append(closing_pivot[['event_id', 'market_slug', 'date', 'yes_closing_price', 'no_closing_price']])
                except Exception as e:
                    # If closing prices can't be loaded, continue without them
                    pass
        
        # Merge closing prices with combined_df
        if all_closing_prices:
            combined_closing_prices = pd.concat(all_closing_prices, ignore_index=True)
            combined_df = combined_df.merge(
                combined_closing_prices,
                on=['event_id', 'market_slug', 'date'],
                how='left'
            )
        else:
            combined_df['yes_closing_price'] = None
            combined_df['no_closing_price'] = None
        
        # Calculate values (yes_net_tokens * yes_closing_price, no_net_tokens * no_closing_price)
        combined_df['yes_value'] = combined_df['yes_net_tokens'] * combined_df['yes_closing_price'].fillna(0)
        combined_df['no_value'] = combined_df['no_net_tokens'] * combined_df['no_closing_price'].fillna(0)
        
        # Group by date and aggregate
        grouped = combined_df.groupby('date').agg({
            'market_id': 'nunique',  # Number of unique markets
            'yes_daily_buy': 'sum',
            'yes_daily_sell': 'sum',
            'no_daily_buy': 'sum',
            'no_daily_sell': 'sum',
            'yes_value': 'sum',  # Sum of yes_value across all markets
            'no_value': 'sum'    # Sum of no_value across all markets
        }).reset_index()
        
        # Rename columns
        grouped.columns = ['date', 'markets_engaged', 'yes_buy', 'yes_sell', 'no_buy', 'no_sell', 'yes_value', 'no_value']
        
        # Calculate net_yes and net_no (buy - sell)
        grouped['net_yes'] = grouped['yes_buy'] - grouped['yes_sell']
        grouped['net_no'] = grouped['no_buy'] - grouped['no_sell']
        
        # Calculate total_token and total_value
        grouped['total_token'] = grouped['net_yes'] + grouped['net_no']
        grouped['total_value'] = grouped['yes_value'] + grouped['no_value']
        
        # Sort by date (earliest to latest) before calculating cumulative values
        grouped = grouped.sort_values('date').reset_index(drop=True)
        
        # Calculate cumulative values (carry forward from previous days)
        grouped['cumulative_yes_value'] = grouped['yes_value'].cumsum()
        grouped['cumulative_no_value'] = grouped['no_value'].cumsum()
        grouped['cumulative_net_yes'] = grouped['net_yes'].cumsum()
        grouped['cumulative_net_no'] = grouped['net_no'].cumsum()
        grouped['cumulative_total_token'] = grouped['total_token'].cumsum()
        grouped['cumulative_total_value'] = grouped['total_value'].cumsum()
        
        # Reorder columns
        output_df = grouped[['date', 'markets_engaged', 'yes_buy', 'yes_sell', 'no_buy', 'no_sell', 
                             'yes_value', 'no_value', 'net_yes', 'net_no',
                             'cumulative_yes_value', 'cumulative_no_value', 'cumulative_net_yes', 'cumulative_net_no',
                             'total_token', 'total_value', 'cumulative_total_token', 'cumulative_total_value']].copy()
        
        # Write to CSV
        output_path = user_dir / "date_group_token.csv"
        output_df.to_csv(output_path, index=False)
        
    except Exception as e:
        print(f"  Error creating date_group_token.csv for user {user_id}: {str(e)}")
        return
