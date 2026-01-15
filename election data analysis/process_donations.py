#!/usr/bin/env python3
"""
Process election donation data and calculate normalized daily donations.

Creates CSV files with day_offset mapping for each candidate.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path
PARENT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PARENT_DIR))

DONATION_CSV = Path(__file__).parent / "Filtered_US_Election_Donation.csv"
OUTPUT_BASE = Path(__file__).parent / "output" / "donations"

# Market closing dates (day_offset = 0)
MARKET_CLOSING_DATE = pd.Timestamp("2024-11-12")

# Setup logging
def log(message: str, level: str = "INFO"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def parse_received_date(received_value):
    """
    Parse MMDDYYYY format date from integer.
    Example: 7312023 -> 2023-07-31
    """
    try:
        received_str = str(int(received_value))
        if len(received_str) == 8:
            # MMDDYYYY format
            month = int(received_str[:2])
            day = int(received_str[2:4])
            year = int(received_str[4:8])
            return pd.Timestamp(year=year, month=month, day=day)
        elif len(received_str) == 7:
            # MDDYYYY format (single digit month)
            month = int(received_str[0])
            day = int(received_str[1:3])
            year = int(received_str[3:7])
            return pd.Timestamp(year=year, month=month, day=day)
        else:
            return None
    except (ValueError, TypeError):
        return None


def process_candidate_donations(candidate_name: str, party: str, alternative_names: list = None) -> pd.DataFrame:
    """
    Process donations for a specific candidate.
    
    Args:
        candidate_name: Primary candidate name to use for logging
        party: Political party
        alternative_names: List of alternative candidate name variations to include
    
    Returns DataFrame with columns: day_offset, date, daily_donation, normalized_donation
    """
    log(f"Processing donations for {candidate_name} ({party})...")
    
    if not DONATION_CSV.exists():
        log(f"Donation CSV not found: {DONATION_CSV}", "ERROR")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(DONATION_CSV, low_memory=False)
    except Exception as e:
        log(f"Error reading donation CSV: {e}", "ERROR")
        return pd.DataFrame()
    
    # Filter for candidate - include primary name and any alternative names
    candidate_names = [candidate_name]
    if alternative_names:
        candidate_names.extend(alternative_names)
    
    candidate_df = df[df['Candidate'].isin(candidate_names)].copy()
    
    if candidate_df.empty:
        log(f"No donations found for {candidate_name} (searched: {', '.join(candidate_names)})", "WARNING")
        return pd.DataFrame()
    
    log(f"Found {len(candidate_df)} donation records (including variations: {', '.join(candidate_names)})")
    
    # Parse dates
    candidate_df['date'] = candidate_df['Received'].apply(parse_received_date)
    
    # Filter out invalid dates
    initial_count = len(candidate_df)
    candidate_df = candidate_df[candidate_df['date'].notna()].copy()
    if len(candidate_df) < initial_count:
        log(f"Filtered {initial_count - len(candidate_df)} records with invalid dates", "WARNING")
    
    if candidate_df.empty:
        log(f"No valid donation dates for {candidate_name}", "WARNING")
        return pd.DataFrame()
    
    # Ensure Donation_Amount_USD is numeric
    candidate_df['Donation_Amount_USD'] = pd.to_numeric(
        candidate_df['Donation_Amount_USD'], 
        errors='coerce'
    )
    
    # Filter out negative donations (refunds) or handle them appropriately
    # For now, we'll include all donations (positive and negative)
    candidate_df = candidate_df[candidate_df['Donation_Amount_USD'].notna()].copy()
    
    # Group by date and sum donations
    daily_donations = candidate_df.groupby('date', as_index=False).agg(
        daily_donation=('Donation_Amount_USD', 'sum')
    )
    
    # Calculate total donations across all dates
    total_donations = daily_donations['daily_donation'].sum()
    
    log(f"Total donations: ${total_donations:,.2f} across {len(daily_donations)} days")
    
    # Calculate normalized donations (daily / total)
    daily_donations['normalized_donation'] = daily_donations['daily_donation'] / total_donations
    
    # Calculate day_offset based on market closing date
    daily_donations['day_offset'] = (
        daily_donations['date'] - MARKET_CLOSING_DATE
    ).dt.days
    
    # Sort by day_offset
    daily_donations = daily_donations.sort_values('day_offset').reset_index(drop=True)
    
    # Select and reorder columns
    result = daily_donations[['day_offset', 'date', 'daily_donation', 'normalized_donation']].copy()
    
    log(f"Date range: {result['date'].min()} to {result['date'].max()}")
    log(f"Day offset range: {result['day_offset'].min()} to {result['day_offset'].max()}")
    
    return result


def main():
    """Main function to process donations for both candidates."""
    log("=" * 80)
    log("Processing Election Donation Data - Wisconsin US Senate Election")
    log("=" * 80)
    
    if not DONATION_CSV.exists():
        log(f"Donation CSV not found: {DONATION_CSV}", "ERROR")
        return
    
    # Create output directory
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
    
    # Process Hovde (Republican) - combine "HOVDE, ERIC" and "HOVDE, ERIC D"
    hovde_df = process_candidate_donations("HOVDE, ERIC", "REP", alternative_names=["HOVDE, ERIC D"])
    if not hovde_df.empty:
        output_path = OUTPUT_BASE / "hovde_donations.csv"
        hovde_df.to_csv(output_path, index=False)
        log(f"Saved Hovde donations to: {output_path}", "SUCCESS")
        log(f"  Total records: {len(hovde_df)}")
    else:
        log("No Hovde donation data to save", "WARNING")
    
    log("")
    
    # Process Baldwin (Democrat)
    baldwin_df = process_candidate_donations("BALDWIN, TAMMY", "DEM")
    if not baldwin_df.empty:
        output_path = OUTPUT_BASE / "baldwin_donations.csv"
        baldwin_df.to_csv(output_path, index=False)
        log(f"Saved Baldwin donations to: {output_path}", "SUCCESS")
        log(f"  Total records: {len(baldwin_df)}")
    else:
        log("No Baldwin donation data to save", "WARNING")
    
    log("=" * 80)
    log("Donation processing completed")
    log(f"Output directory: {OUTPUT_BASE}")
    log("=" * 80)


if __name__ == "__main__":
    main()



