"""
Script to analyze market timelines for each event and market.

For each event in the raw folder, for each market:
- Number of trades (from trades CSV)
- First trade timestamp (from trades CSV)
- Last trade timestamp (from trades CSV)
- Market open timestamp (first price action from prices CSV)
- Market close timestamp (last price action from prices CSV)
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def analyze_trades_file(trades_file):
    """
    Analyze a trades CSV file to extract trade statistics.
    
    Args:
        trades_file: Path to trades CSV file
        
    Returns:
        Dictionary with trade statistics or None if file doesn't exist/empty
    """
    if not trades_file.exists():
        return None
    
    try:
        df = pd.read_csv(trades_file, low_memory=False)
        
        if df.empty:
            return {
                'num_trades': 0,
                'first_trade_timestamp': None,
                'last_trade_timestamp': None,
                'first_trade_datetime': None,
                'last_trade_datetime': None
            }
        
        # Convert timestamp to numeric (in case it's stored as string)
        df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        
        if df.empty:
            return {
                'num_trades': 0,
                'first_trade_timestamp': None,
                'last_trade_timestamp': None,
                'first_trade_datetime': None,
                'last_trade_datetime': None
            }
        
        num_trades = len(df)
        first_trade_ts = int(df['timestamp'].min())
        last_trade_ts = int(df['timestamp'].max())
        
        # Convert to datetime strings
        first_trade_dt = datetime.fromtimestamp(first_trade_ts).strftime('%Y-%m-%d %H:%M:%S UTC')
        last_trade_dt = datetime.fromtimestamp(last_trade_ts).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return {
            'num_trades': num_trades,
            'first_trade_timestamp': first_trade_ts,
            'last_trade_timestamp': last_trade_ts,
            'first_trade_datetime': first_trade_dt,
            'last_trade_datetime': last_trade_dt
        }
    except Exception as e:
        print(f"Error reading {trades_file}: {e}")
        return None


def analyze_prices_file(prices_file, market_slug):
    """
    Analyze a prices CSV file to extract market open/close timestamps.
    Filters by market_slug if provided.
    
    Args:
        prices_file: Path to prices CSV file
        market_slug: Market slug to filter by (optional)
        
    Returns:
        Dictionary with market open/close statistics or None
    """
    if not prices_file.exists():
        return None
    
    try:
        df = pd.read_csv(prices_file, low_memory=False)
        
        if df.empty:
            return {
                'market_open_timestamp': None,
                'market_close_timestamp': None,
                'market_open_datetime': None,
                'market_close_datetime': None
            }
        
        # Filter by market_slug if provided and column exists
        if market_slug and 'market_slug' in df.columns:
            df = df[df['market_slug'] == market_slug]
        
        if df.empty:
            return {
                'market_open_timestamp': None,
                'market_close_timestamp': None,
                'market_open_datetime': None,
                'market_close_datetime': None
            }
        
        # Convert timestamp to numeric
        df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        
        if df.empty:
            return {
                'market_open_timestamp': None,
                'market_close_timestamp': None,
                'market_open_datetime': None,
                'market_close_datetime': None
            }
        
        market_open_ts = int(df['timestamp'].min())
        market_close_ts = int(df['timestamp'].max())
        
        # Convert to datetime strings
        market_open_dt = datetime.fromtimestamp(market_open_ts).strftime('%Y-%m-%d %H:%M:%S UTC')
        market_close_dt = datetime.fromtimestamp(market_close_ts).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return {
            'market_open_timestamp': market_open_ts,
            'market_close_timestamp': market_close_ts,
            'market_open_datetime': market_open_dt,
            'market_close_datetime': market_close_dt
        }
    except Exception as e:
        print(f"Error reading {prices_file}: {e}")
        return None


def find_prices_file_for_market(event_dir, market_slug):
    """
    Find the prices CSV file for a given market.
    Prices files may contain multiple markets, so we need to check which file contains this market.
    
    Args:
        event_dir: Path to event directory
        market_slug: Market slug to find
        
    Returns:
        Path to prices file or None
    """
    prices_dir = event_dir / "prices"
    
    if not prices_dir.exists():
        return None
    
    # Check all price files to see which one contains this market
    for price_file in prices_dir.glob("*_price.csv"):
        try:
            df = pd.read_csv(price_file, low_memory=False, nrows=1)
            if 'market_slug' in df.columns:
                # Read more rows to check if this market is in the file
                df_full = pd.read_csv(price_file, low_memory=False)
                if market_slug in df_full['market_slug'].values:
                    return price_file
            else:
                # If no market_slug column, assume filename matches market
                # Extract market slug from filename
                file_market_slug = price_file.stem.replace('_price', '')
                if file_market_slug == market_slug:
                    return price_file
        except Exception:
            continue
    
    return None


def analyze_all_markets(base_path="raw"):
    """
    Analyze all events and markets in the raw data directory.
    
    Args:
        base_path: Base path to raw data directory (default: "raw")
        
    Returns:
        List of dictionaries with market analysis results
    """
    base_dir = Path(base_path)
    
    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist")
        return []
    
    results = []
    
    # Walk through all event directories
    for event_dir in sorted(base_dir.iterdir()):
        if not event_dir.is_dir() or event_dir.name.startswith('.'):
            continue
        
        event_id = event_dir.name
        trades_dir = event_dir / "trades"
        
        if not trades_dir.exists():
            print(f"Warning: No trades directory found for event {event_id}")
            continue
        
        # Find all trade CSV files in this event
        trade_files = list(trades_dir.glob("*_trades.csv"))
        
        if not trade_files:
            print(f"Warning: No trade CSV files found for event {event_id}")
            continue
        
        print(f"Processing event: {event_id} ({len(trade_files)} market(s))...")
        
        # Process each market
        for trade_file in sorted(trade_files):
            market_slug = trade_file.stem.replace('_trades', '')
            
            # Analyze trades
            trades_info = analyze_trades_file(trade_file)
            
            if trades_info is None:
                print(f"  Warning: Could not analyze trades for {market_slug}")
                continue
            
            # Find and analyze prices
            prices_file = find_prices_file_for_market(event_dir, market_slug)
            prices_info = None
            
            if prices_file:
                prices_info = analyze_prices_file(prices_file, market_slug)
            else:
                # Try to find a price file with matching name
                prices_dir = event_dir / "prices"
                if prices_dir.exists():
                    potential_price_file = prices_dir / f"{market_slug}_price.csv"
                    if potential_price_file.exists():
                        prices_info = analyze_prices_file(potential_price_file, market_slug)
            
            # Combine results
            market_result = {
                'event_id': event_id,
                'market_slug': market_slug,
                'trades_file': str(trade_file.relative_to(base_dir)),
                'prices_file': str(prices_file.relative_to(base_dir)) if prices_file else None,
                'num_trades': trades_info['num_trades'],
                'first_trade_timestamp': trades_info['first_trade_timestamp'],
                'last_trade_timestamp': trades_info['last_trade_timestamp'],
                'first_trade_datetime': trades_info['first_trade_datetime'],
                'last_trade_datetime': trades_info['last_trade_datetime'],
                'market_open_timestamp': prices_info['market_open_timestamp'] if prices_info else None,
                'market_close_timestamp': prices_info['market_close_timestamp'] if prices_info else None,
                'market_open_datetime': prices_info['market_open_datetime'] if prices_info else None,
                'market_close_datetime': prices_info['market_close_datetime'] if prices_info else None,
            }
            
            results.append(market_result)
    
    return results


def generate_report(results, output_file="market_timeline_analysis.md"):
    """
    Generate a markdown report of market timeline analysis.
    
    Args:
        results: List of market analysis dictionaries
        output_file: Output file path
    """
    lines = []
    
    lines.append("# Market Timeline Analysis\n")
    lines.append("\n")
    lines.append("This report provides a comprehensive timeline analysis for each market across all events.\n")
    lines.append("\n")
    lines.append("## Summary\n")
    lines.append("\n")
    
    total_markets = len(results)
    total_trades = sum(r['num_trades'] for r in results)
    markets_with_prices = sum(1 for r in results if r['market_open_timestamp'] is not None)
    
    lines.append(f"- **Total markets analyzed**: {total_markets}")
    lines.append(f"- **Total trades across all markets**: {total_trades:,}")
    lines.append(f"- **Markets with price data**: {markets_with_prices}")
    lines.append(f"- **Markets without price data**: {total_markets - markets_with_prices}\n")
    lines.append("\n")
    
    # Group by event
    events_dict = defaultdict(list)
    for result in results:
        events_dict[result['event_id']].append(result)
    
    lines.append("## Market Timeline by Event\n")
    lines.append("\n")
    
    # Sort events by number of markets
    sorted_events = sorted(events_dict.items(), key=lambda x: len(x[1]), reverse=True)
    
    for event_id, markets in sorted_events:
        lines.append(f"### Event: `{event_id}`\n")
        lines.append("\n")
        lines.append(f"**Number of markets**: {len(markets)}\n")
        lines.append("\n")
        
        # Calculate event-level statistics
        event_total_trades = sum(m['num_trades'] for m in markets)
        event_first_trade = min((m['first_trade_timestamp'] for m in markets if m['first_trade_timestamp']), default=None)
        event_last_trade = max((m['last_trade_timestamp'] for m in markets if m['last_trade_timestamp']), default=None)
        event_market_open = min((m['market_open_timestamp'] for m in markets if m['market_open_timestamp']), default=None)
        event_market_close = max((m['market_close_timestamp'] for m in markets if m['market_close_timestamp']), default=None)
        
        lines.append("**Event-level Statistics:**\n")
        lines.append(f"- Total trades: {event_total_trades:,}\n")
        if event_first_trade:
            lines.append(f"- First trade across all markets: {datetime.fromtimestamp(event_first_trade).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        if event_last_trade:
            lines.append(f"- Last trade across all markets: {datetime.fromtimestamp(event_last_trade).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        if event_market_open:
            lines.append(f"- Market open (earliest): {datetime.fromtimestamp(event_market_open).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        if event_market_close:
            lines.append(f"- Market close (latest): {datetime.fromtimestamp(event_market_close).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        lines.append("\n")
        
        lines.append("| Market Slug | Trades | First Trade | Last Trade | Market Open | Market Close |\n")
        lines.append("| ----------- | ------ | ----------- | ---------- | ----------- | ------------ |\n")
        
        # Sort markets by number of trades (descending)
        sorted_markets = sorted(markets, key=lambda x: x['num_trades'], reverse=True)
        
        for market in sorted_markets:
            market_slug = market['market_slug']
            num_trades = market['num_trades']
            first_trade = market['first_trade_datetime'] or "N/A"
            last_trade = market['last_trade_datetime'] or "N/A"
            market_open = market['market_open_datetime'] or "N/A"
            market_close = market['market_close_datetime'] or "N/A"
            
            lines.append(f"| `{market_slug}` | {num_trades:,} | {first_trade} | {last_trade} | {market_open} | {market_close} |\n")
        
        lines.append("\n")
    
    # Detailed table with all markets
    lines.append("## Detailed Market Timeline Table\n")
    lines.append("\n")
    lines.append("| Event ID | Market Slug | Trades | First Trade (UTC) | Last Trade (UTC) | Market Open (UTC) | Market Close (UTC) |\n")
    lines.append("| -------- | ----------- | ------ | ----------------- | ---------------- | ----------------- | ------------------ |\n")
    
    # Sort all results by event_id, then by num_trades
    sorted_results = sorted(results, key=lambda x: (x['event_id'], -x['num_trades']))
    
    for result in sorted_results:
        event_id = result['event_id']
        market_slug = result['market_slug']
        num_trades = result['num_trades']
        first_trade = result['first_trade_datetime'] or "N/A"
        last_trade = result['last_trade_datetime'] or "N/A"
        market_open = result['market_open_datetime'] or "N/A"
        market_close = result['market_close_datetime'] or "N/A"
        
        lines.append(f"| `{event_id}` | `{market_slug}` | {num_trades:,} | {first_trade} | {last_trade} | {market_open} | {market_close} |\n")
    
    lines.append("\n")
    
    # Write report
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Report generated: {output_file}")
    return output_file


def main():
    """Main function to run the analysis."""
    print("Analyzing market timelines...")
    print()
    
    results = analyze_all_markets()
    
    if not results:
        print("No markets found to analyze.")
        return
    
    print(f"\nAnalysis complete: {len(results)} markets analyzed")
    
    # Generate markdown report
    report_file = generate_report(results)
    print(f"\nDetailed report saved to: {report_file}")


if __name__ == "__main__":
    main()
