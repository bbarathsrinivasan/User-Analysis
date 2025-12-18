"""
Script to analyze events/markets with incomplete data due to reaching the 1,000,000 row threshold.

This script identifies CSV files in the raw data directory that have exactly 1,000,000 data rows
(1,000,001 total rows including header), indicating they hit the export limit and may have incomplete data.
"""
import os
from pathlib import Path
from collections import defaultdict


# Threshold for incomplete data detection
MAX_THRESHOLD = 1000000


def count_csv_rows(file_path):
    """
    Count the number of rows in a CSV file.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        Tuple of (total_rows, data_rows) where data_rows = total_rows - 1 (header)
    """
    try:
        # Use wc -l equivalent: count newlines
        with open(file_path, 'rb') as f:
            count = sum(1 for _ in f)
        # Subtract 1 for header row to get data rows
        data_rows = count - 1
        return count, data_rows
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None, None


def analyze_incomplete_markets(base_path="raw", threshold=MAX_THRESHOLD):
    """
    Scan all CSV files in the raw data directory and identify those that hit the threshold.
    
    Args:
        base_path: Base path to raw data directory (default: "raw")
        threshold: Maximum row threshold (default: 1,000,000)
        
    Returns:
        Dictionary with event_id as key and list of incomplete markets as value
    """
    base_dir = Path(base_path)
    
    if not base_dir.exists():
        print(f"Error: Directory {base_dir} does not exist")
        return {}
    
    incomplete_markets = defaultdict(list)
    all_markets_info = []
    
    # Walk through all event directories
    for event_dir in sorted(base_dir.iterdir()):
        if not event_dir.is_dir() or event_dir.name.startswith('.'):
            continue
        
        event_id = event_dir.name
        trades_dir = event_dir / "trades"
        
        if not trades_dir.exists():
            continue
        
        # Check all trade CSV files in this event
        for csv_file in sorted(trades_dir.glob("*_trades.csv")):
            total_rows, data_rows = count_csv_rows(csv_file)
            
            if total_rows is None:
                continue
            
            market_slug = csv_file.stem.replace('_trades', '')
            
            market_info = {
                'event_id': event_id,
                'market_slug': market_slug,
                'file_path': str(csv_file.relative_to(base_dir)),
                'total_rows': total_rows,
                'data_rows': data_rows,
                'is_incomplete': data_rows >= threshold
            }
            
            all_markets_info.append(market_info)
            
            if market_info['is_incomplete']:
                incomplete_markets[event_id].append(market_info)
    
    return incomplete_markets, all_markets_info


def get_market_statistics(market_info_list):
    """
    Calculate statistics for markets that hit the threshold.
    
    Args:
        market_info_list: List of market info dictionaries
        
    Returns:
        Dictionary with statistics
    """
    if not market_info_list:
        return {}
    
    total_markets = len(market_info_list)
    total_rows = sum(m['data_rows'] for m in market_info_list)
    avg_rows = total_rows / total_markets if total_markets > 0 else 0
    
    return {
        'total_markets': total_markets,
        'total_data_rows': total_rows,
        'average_rows_per_market': avg_rows,
        'all_at_threshold': all(m['data_rows'] == MAX_THRESHOLD for m in market_info_list)
    }


def generate_report(incomplete_markets, all_markets_info, output_file="incomplete_data_analysis.md"):
    """
    Generate a markdown report of incomplete markets.
    
    Args:
        incomplete_markets: Dictionary of incomplete markets by event
        all_markets_info: List of all market info dictionaries
        output_file: Output file path
    """
    lines = []
    
    lines.append("# Analysis of Markets with Incomplete Data\n")
    lines.append("\n")
    lines.append("This report identifies events and markets where data export reached the maximum threshold of **1,000,000 rows**, indicating potentially incomplete data.\n")
    lines.append("\n")
    lines.append("## Summary\n")
    lines.append("\n")
    
    total_incomplete = sum(len(markets) for markets in incomplete_markets.values())
    total_events_with_incomplete = len(incomplete_markets)
    total_markets_analyzed = len(all_markets_info)
    
    lines.append(f"- **Total markets analyzed**: {total_markets_analyzed}")
    lines.append(f"- **Markets with incomplete data**: {total_incomplete}")
    lines.append(f"- **Events with incomplete markets**: {total_events_with_incomplete}")
    lines.append(f"- **Threshold**: {MAX_THRESHOLD:,} data rows (1,000,001 total rows including header)\n")
    lines.append("\n")
    
    if total_incomplete == 0:
        lines.append("✅ **No markets found with incomplete data.**\n")
        lines.append("\n")
    else:
        lines.append("⚠️ **Warning**: The following markets have reached the export limit and may have incomplete data.\n")
        lines.append("\n")
        
        lines.append("## Events with Incomplete Markets\n")
        lines.append("\n")
        
        # Sort events by number of incomplete markets (descending)
        sorted_events = sorted(incomplete_markets.items(), key=lambda x: len(x[1]), reverse=True)
        
        for event_id, markets in sorted_events:
            lines.append(f"### Event: `{event_id}`\n")
            lines.append("\n")
            lines.append(f"**Number of incomplete markets**: {len(markets)}\n")
            lines.append("\n")
            
            # Calculate statistics for this event
            stats = get_market_statistics(markets)
            lines.append(f"- Total data rows across incomplete markets: {stats['total_data_rows']:,}")
            lines.append(f"- Average rows per market: {stats['average_rows_per_market']:,.0f}")
            if stats['all_at_threshold']:
                lines.append("- ⚠️ **All markets in this event are exactly at the threshold**\n")
            lines.append("\n")
            
            lines.append("| Market Slug | File Path | Data Rows | Status |\n")
            lines.append("| ----------- | --------- | --------- | ------ |\n")
            
            for market in sorted(markets, key=lambda x: x['data_rows'], reverse=True):
                status = "⚠️ AT LIMIT" if market['data_rows'] == MAX_THRESHOLD else f"⚠️ EXCEEDS ({market['data_rows']:,})"
                lines.append(f"| `{market['market_slug']}` | `{market['file_path']}` | {market['data_rows']:,} | {status} |\n")
            
            lines.append("\n")
        
        lines.append("## Detailed Breakdown\n")
        lines.append("\n")
        lines.append("### All Markets Analyzed\n")
        lines.append("\n")
        lines.append("| Event ID | Market Slug | Data Rows | Status |\n")
        lines.append("| -------- | ----------- | --------- | ------ |\n")
        
        # Sort all markets by data rows (descending)
        sorted_all = sorted(all_markets_info, key=lambda x: x['data_rows'], reverse=True)
        
        for market in sorted_all:
            if market['is_incomplete']:
                status = "⚠️ INCOMPLETE"
            else:
                status = "✅ Complete"
            lines.append(f"| `{market['event_id']}` | `{market['market_slug']}` | {market['data_rows']:,} | {status} |\n")
        
        lines.append("\n")
        
        lines.append("## Recommendations\n")
        lines.append("\n")
        lines.append("1. **Re-export data** for markets marked as incomplete, using pagination or date filters to retrieve all records.")
        lines.append("2. **Verify completeness** by checking if the last row timestamp matches the expected end date for each market.")
        lines.append("3. **Consider data partitioning** for very large markets to avoid hitting export limits in the future.")
        lines.append("4. **Monitor export processes** to ensure all data is captured before the threshold is reached.\n")
        lines.append("\n")
    
    # Write report
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Report generated: {output_file}")
    return output_file


def main():
    """Main function to run the analysis."""
    print("Analyzing markets for incomplete data...")
    print(f"Threshold: {MAX_THRESHOLD:,} data rows\n")
    
    incomplete_markets, all_markets_info = analyze_incomplete_markets()
    
    total_incomplete = sum(len(markets) for markets in incomplete_markets.values())
    
    print(f"\nAnalysis complete:")
    print(f"  - Total markets analyzed: {len(all_markets_info)}")
    print(f"  - Markets with incomplete data: {total_incomplete}")
    print(f"  - Events with incomplete markets: {len(incomplete_markets)}")
    
    if total_incomplete > 0:
        print(f"\nEvents with incomplete markets:")
        for event_id, markets in sorted(incomplete_markets.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  - {event_id}: {len(markets)} market(s)")
            for market in markets:
                print(f"    * {market['market_slug']}: {market['data_rows']:,} rows")
    
    # Generate markdown report
    report_file = generate_report(incomplete_markets, all_markets_info)
    print(f"\nDetailed report saved to: {report_file}")


if __name__ == "__main__":
    main()
