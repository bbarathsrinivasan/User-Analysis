# Election Data Analysis Pipeline

## Overview

This pipeline processes market trade data for the **arizona-us-senate-election-winner** event and generates segment-based aggregation files with comparison graphs. The pipeline compares investment-based odds (from user trading behavior) with price-based market odds and election donation patterns.

### Key Statistics

**Election Donations**:
- **GALLEGO, RUBEN (Democrat)**: $32,183,439.00 total donations
- **LAKE, KARI (Republican)**: $12,059,627.00 total donations

**Market Trading Activity**:
- **Democrat market**: 5,887,500 trades across 2 days
- **Republican market**: 11,313,000 trades across 3 days
- **Other Party market**: 6,751,500 trades across 13 days

## Pipeline Architecture

The pipeline consists of **three main scripts** that run sequentially:

1. **`build_segment_positions.py`** - Processes raw trades and creates per-user position files
2. **`process_donations.py`** - Processes election donation data and calculates normalized donations
3. **`build_segment_aggregation.py`** - Aggregates positions by segment and generates comparison graphs

---

## Step 1: Build Segment Positions (`build_segment_positions.py`)

### Purpose
Process raw trade data from the `data` folder and create per-user, per-market position files that will be used for segment aggregation.

### Input Structure
```
../data/
└── arizona-us-senate-election-winner/
    ├── trades/
    │   └── <market_slug>_trades.csv
    └── prices/
        └── <market_slug>_price.csv
```

### Trade CSV Format
Expected columns in `*_trades.csv`:
- `proxyWallet` - User identifier
- `side` - Trade side (BUY/SELL)
- `size` - Trade quantity
- `timestamp` - Unix timestamp
- `slug` - Market slug
- `eventSlug` - Event identifier
- `outcome` - Token type (Yes/No)

### Processing Logic

1. **Load Market Trades**
   - Read trade CSV file
   - Map columns: `proxyWallet` → `user_id`, `outcome` → `token_type` (YES/NO)
   - Convert timestamps to UTC dates
   - Filter out invalid data

2. **Compute Day Offset**
   - For each market, find the maximum date (closing date = day_offset 0)
   - Calculate day_offset: `(date - closing_date).days`
   - Earlier days have negative offsets
   - **Example**: If closing date is 2024-11-12:
     - 2024-11-12 → day_offset = 0
     - 2024-11-11 → day_offset = -1
     - 2024-11-10 → day_offset = -2

3. **Build Daily User Token Series**
   - Aggregate trades by: `(user_id, token_type, day_offset)`
   - Calculate:
     - `daily_buy` - Sum of BUY quantities
     - `daily_sell` - Sum of SELL quantities
     - `net_tokens` - daily_buy - daily_sell
   - Get end-of-day timestamp for each day

4. **Build Per-User Market DataFrame**
   - For each user in each market:
     - Fill all days from first trade day to closing day (day_offset 0)
     - Calculate cumulative positions:
       - `yes_cumulative_position` = cumulative sum of yes_net_tokens
       - `no_cumulative_position` = cumulative sum of no_net_tokens
     - Calculate H_y and H_n (same as cumulative positions)
     - Calculate individual positions:
       - `individual_yes_position` = H_y (if H_y > 0) + (-H_n) (if H_n < 0)
       - `individual_no_position` = H_n (if H_n > 0) + (-H_y) (if H_y < 0)

### Output Structure
```
output/segment_positions/
└── arizona-us-senate-election-winner/
    └── <market_slug>/
        └── user_<user_id>.csv
```

### Output CSV Format (`user_<user_id>.csv`)
Columns:
- `day_offset` - Days from closing (0 = closing day)
- `timestamp` - End-of-day timestamp
- `date` - Calendar date
- `yes_daily_buy`, `yes_daily_sell`, `yes_net_tokens`, `yes_cumulative_position`
- `no_daily_buy`, `no_daily_sell`, `no_net_tokens`, `no_cumulative_position`
- `H_y`, `H_n` - Per-market cumulative positions
- `individual_yes_position`, `individual_no_position` - Individual position calculations

---

## Step 2: Process Donations (`process_donations.py`)

### Purpose
Process election donation data and calculate normalized daily donations for each candidate, mapped to day_offset for comparison with market data.

### Input
- `US_Election_Donation.csv` with columns:
  - `Party` - Political party (DEM/REP)
  - `Candidate` - Candidate name
  - `Received` - Date in MMDDYYYY format (e.g., 7312023 = July 31, 2023)
  - `Donation_Amount_USD` - Donation amount in USD

### Processing Logic

1. **Load Donation Data**
   - Read `US_Election_Donation.csv`
   - Filter for "GALLEGO, RUBEN" (Democrat) and "LAKE, KARI" (Republican)

2. **Parse Dates**
   - Convert "Received" column from MMDDYYYY format to datetime
   - Handle both 7-digit (MDDYYYY) and 8-digit (MMDDYYYY) formats
   - Filter out invalid dates

3. **Calculate Daily Donations**
   - Group by date and sum `Donation_Amount_USD`
   - Calculate total donations across all dates

4. **Normalize Donations**
   - Calculate: `normalized_donation = daily_donation / total_donation`
   - This gives the proportion of total donations received on each day

5. **Map to Day Offset**
   - Market closing date: 2024-11-12 (day_offset = 0)
   - Calculate: `day_offset = (donation_date - closing_date).days`
   - This allows alignment with market trading data

### Output Structure
```
output/donations/
├── gallego_donations.csv
└── lake_donations.csv
```

### Output CSV Format
Columns:
- `day_offset` - Days from market closing (0 = closing day)
- `date` - Calendar date of donation
- `daily_donation` - Total USD donated on that day
- `normalized_donation` - Daily donation / Total donations (proportion)

### Total Donation Amounts

**GALLEGO, RUBEN (Democrat)**:
- **Total donations**: $32,183,439.00
- **Donation period**: 914 days (2022-04-08 to 2025-06-30)
- **Average daily donation**: $35,211.64

**LAKE, KARI (Republican)**:
- **Total donations**: $12,059,627.00
- **Donation period**: 637 days (2023-07-24 to 2025-06-30)
- **Average daily donation**: $18,921.55

**Note**: Gallego received approximately **2.67x more** in total donations than Lake.

---

## Step 3: Build Segment Aggregation (`build_segment_aggregation.py`)

### Purpose
Aggregate individual user positions by segment (Small, Medium, Large) and create comparison graphs showing investment-based odds vs. price-based market odds vs. election donations.

### Input Requirements

1. **Segment Output** (from Step 1)
   - `output/segment_positions/<event_id>/<market_slug>/user_*.csv` files

2. **Segment Mapping**
   - `../all_users_analysis.csv` file with columns:
     - `user_id` - User identifier
     - `user_segment` - Segment classification (Small, Medium, or Large)

3. **Price Data** (for market odds)
   - `../data/<event_id>/prices/<market_slug>_price.csv` or `*_closing_prices.csv`

4. **Donation Data** (from Step 2)
   - `output/donations/gallego_donations.csv` (for Democrat markets)
   - `output/donations/lake_donations.csv` (for Republican markets)

### Processing Logic

1. **Load Segment Mapping**
   - Read `all_users_analysis.csv`
   - Create dictionary: `user_id → user_segment`
   - Segment thresholds:
     - **Large**: `cumulative_total_value_max` ≥ 1,000,000
     - **Medium**: 10,000 ≤ `cumulative_total_value_max` < 1,000,000
     - **Small**: `cumulative_total_value_max` < 10,000

2. **Aggregate Market Segments**
   - For each market:
     - Load all user CSV files from `output/segment_positions`
     - Map each user to their segment using the segment mapping
     - For each day_offset:
       - Aggregate YES positions: Sum `individual_yes_position` for users where `yes_cumulative_position != 0`
       - Aggregate NO positions: Sum `individual_no_position` for users where `no_cumulative_position != 0`
       - Calculate odds: `agg_yes / (agg_yes + agg_no)`
     - Create 4 DataFrames:
       - `all_segments` - All users combined
       - `small_segment` - Only Small segment users
       - `medium_segment` - Only Medium segment users
       - `large_segment` - Only Large segment users

3. **Load Price Odds** (Market Odds)
   - Get market closing date from user files (day_offset = 0)
   - Load price file and filter YES prices
   - Get end-of-day price for each date (last price by timestamp)
   - Convert dates to day_offset
   - Filter prices with day_offset <= 0 (only prices up to closing date)

4. **Load Donation Data**
   - Determine candidate based on market slug:
     - "will-a-democrat-win" → Gallego donations
     - "will-a-republican-win" → Lake donations
   - Load corresponding donation CSV

5. **Create Comparison Graphs** (3 graphs per market)
   - **Graph 1: Original** (`odds_comparison_original.png`)
     - 5 lines: Price-based + 4 investment-based (no donations)
   - **Graph 2: Donations** (`odds_comparison_donations.png`)
     - 1 line: Election Donations (Normalized)
     - Only created for Democrat and Republican markets
   - **Graph 3: Combined** (`odds_comparison.png`)
     - 6 lines: All 5 original lines + donation line

### Output Structure
```
output/segment_aggregation/
└── arizona-us-senate-election-winner/
    └── <market_slug>/
        ├── all_segments.csv
        ├── small_segment.csv
        ├── medium_segment.csv
        ├── large_segment.csv
        ├── odds_comparison_original.png
        ├── odds_comparison_donations.png (if applicable)
        └── odds_comparison.png
```

### Output CSV Format
Each CSV file has columns:
- `day_offset` - Days from closing (0 = closing day)
- `agg_yes` - Aggregated YES positions
- `agg_no` - Aggregated NO positions
- `odds` - Calculated odds (agg_yes / (agg_yes + agg_no))

---

## How Trades Are Split Across Days

### Day Offset Calculation

The pipeline uses a **day_offset** system to align all data points relative to the market closing date:

```
day_offset = (trade_date - market_closing_date).days
```

Where:
- **Market closing date** = The last trading date (maximum date in the market's trade data)
- **day_offset = 0** = Closing day
- **day_offset < 0** = Days before closing (earlier days)
- **day_offset > 0** = Days after closing (should not occur in valid data)

### Example: Arizona US Senate Election Markets

#### Democrat Market (`will-a-democrat-win-arizona-us-senate-election`)
- **Total trades**: 5,887,500
- **Trading period**: 2 days
- **Date range**: 2024-11-11 to 2024-11-12
- **Day offsets**: -1, 0
  - **Day -1 (2024-11-11)**: 5,887,317 trades (99.997%)
  - **Day 0 (2024-11-12)**: 183 trades (0.003%) - Closing day

#### Republican Market (`will-a-republican-win-arizona-us-senate-election`)
- **Total trades**: 11,313,000
- **Trading period**: 3 days
- **Date range**: 2024-11-10 to 2024-11-12
- **Day offsets**: -2, -1, 0
  - **Day -2 (2024-11-10)**: 588,224 trades (5.20%)
  - **Day -1 (2024-11-11)**: 10,724,725 trades (94.80%)
  - **Day 0 (2024-11-12)**: 51 trades (0.00%) - Closing day

#### Other Party Market (`will-a-candidate-from-another-party-win-arizona-us-senate-election`)
- **Total trades**: 6,751,500
- **Trading period**: 13 days
- **Date range**: 2024-10-31 to 2024-11-12
- **Day offsets**: -12 to 0
  - **Day -12 (2024-10-31)**: 1,269,094 trades (18.80%)
  - **Day -11 (2024-11-01)**: 540,040 trades (8.00%)
  - **Day -10 (2024-11-02)**: 472,535 trades (7.00%)
  - **Day -9 to -7**: Various amounts
  - **Day -6 (2024-11-06)**: 3,834,774 trades (56.80%) - Peak trading day
  - **Day -5 to 0**: Decreasing activity

### Key Observations

1. **Trading Concentration**: Most markets show heavy concentration of trades on specific days:
   - Democrat market: 99.997% of trades on day -1
   - Republican market: 94.80% of trades on day -1
   - Other Party market: 56.80% of trades on day -6

2. **Short Trading Windows**: Some markets have very short active trading periods:
   - Democrat: Only 2 days of trading
   - Republican: Only 3 days of trading
   - This explains why aggregated outputs show few day_offset values

3. **Day Offset Alignment**: All data (trades, prices, donations) is aligned using day_offset, allowing:
   - Comparison across different time scales
   - Alignment of donation patterns with trading activity
   - Historical analysis relative to closing date

### Daily Aggregation Process

For each day_offset, the pipeline:

1. **Collects all trades** that occurred on that calendar date
2. **Groups by user and token type** (YES/NO)
3. **Calculates daily totals**:
   - `daily_buy` = Sum of all BUY quantities
   - `daily_sell` = Sum of all SELL quantities
   - `net_tokens` = daily_buy - daily_sell
4. **Computes cumulative positions** by summing net_tokens from first trade day to current day
5. **Calculates individual positions** using the formulas:
   - `individual_yes_position` = H_y (if > 0) + (-H_n) (if < 0)
   - `individual_no_position` = H_n (if > 0) + (-H_y) (if < 0)

### Why Some Markets Show Few Days

The aggregated CSV files show only the days where trading actually occurred. For example:
- **Democrat market**: Only 2 days because all 5.9M trades happened on just 2 calendar dates
- **Republican market**: Only 3 days because all 11.3M trades happened on 3 calendar dates

This is **correct behavior** - the pipeline accurately reflects the actual trading activity, which was highly concentrated in short time periods for these markets.

---

## Graph Types Generated

### 1. Original Graph (`odds_comparison_original.png`)
Shows 5 lines comparing different odds calculations:
- **Blue line**: Price-based Market Odds (from actual trading prices)
- **Green line**: All Segments (Investment-based odds from all users)
- **Orange line**: Small Segment (Investment-based odds)
- **Red line**: Medium Segment (Investment-based odds)
- **Purple line**: Large Segment (Investment-based odds)

### 2. Donations Graph (`odds_comparison_donations.png`)
Shows normalized election donations over time:
- **Brown line**: Election Donations (Normalized) - Daily donation / Total donations
- Y-axis: Normalized Donation (0 to 1 scale)
- Only created for Democrat and Republican markets

### 3. Combined Graph (`odds_comparison.png`)
Shows all 6 lines together:
- All 5 original lines + donation line
- Allows comparison of donation patterns with market odds

---

## Running the Pipeline

### Prerequisites

1. **Python Environment** with packages:
   - pandas >= 2.0.0
   - matplotlib
   - numpy

2. **Required Files** (in parent directory):
   - `data/arizona-us-senate-election-winner/` folder with trades and prices
   - `all_users_analysis.csv` with user segment mappings
   - `US_Election_Donation.csv` in this directory

### Execution Steps

```bash
cd "election data analysis"

# Step 1: Process trades and create per-user position files
python build_segment_positions.py

# Step 2: Process donation data
python process_donations.py

# Step 3: Generate segment aggregations and graphs
python build_segment_aggregation.py
```

### Expected Output

- `output/segment_positions/` - Per-user position files
- `output/donations/` - Normalized donation data
- `output/segment_aggregation/` - Segment aggregations and comparison graphs

---

## Logging Features

All scripts include detailed logging:

- **Timestamped messages** - Every log entry includes timestamp
- **Progress tracking** - Shows current/total items with percentage
- **Remaining work** - Displays how many items are left to process
- **Processing time** - Shows elapsed time for each market
- **Success/Error indicators** - Clear status messages

### Log Levels

- `INFO` - General information
- `PROGRESS` - Progress updates
- `SUCCESS` - Successful operations
- `WARNING` - Warnings (non-fatal)
- `ERROR` - Errors (fatal)

---

## Key Formulas

### Individual Position Calculation
For each user on each day:

```
H_y = yes_cumulative_position
H_n = no_cumulative_position

individual_yes_position = 
    if H_y > 0: H_y
    if H_n < 0: -H_n
    (sum both if both conditions true)

individual_no_position = 
    if H_n > 0: H_n
    if H_y < 0: -H_y
    (sum both if both conditions true)
```

### Segment Aggregation
For each segment and day_offset:

```
agg_yes = sum(individual_yes_position) for users where yes_cumulative_position != 0
agg_no = sum(individual_no_position) for users where no_cumulative_position != 0
odds = agg_yes / (agg_yes + agg_no)
```

### Day Offset Calculation
```
closing_date = max(date) in market trades
day_offset = (date - closing_date).days
```
- Closing day = day_offset 0
- Earlier days = negative day_offset

### Donation Normalization
```
normalized_donation = daily_donation / total_all_donations
```
- Shows proportion of total donations received on each day
- Values range from 0 to 1

---

## Market-Specific Details

### Arizona US Senate Election Winner Markets

1. **Democrat Market** (`will-a-democrat-win-arizona-us-senate-election`)
   - Candidate: GALLEGO, RUBEN
   - Trading: 2 days (5.9M trades)
   - Donation data: Gallego donations
     - Total donations: **$32,183,439.00**
     - Donation period: 914 days (2022-04-08 to 2025-06-30)

2. **Republican Market** (`will-a-republican-win-arizona-us-senate-election`)
   - Candidate: LAKE, KARI
   - Trading: 3 days (11.3M trades)
   - Donation data: Lake donations
     - Total donations: **$12,059,627.00**
     - Donation period: 637 days (2023-07-24 to 2025-06-30)

3. **Other Party Market** (`will-a-candidate-from-another-party-win-arizona-us-senate-election`)
   - No specific candidate
   - Trading: 13 days (6.8M trades)
   - No donation data (not candidate-specific)

---

## Troubleshooting

### Error: Data base directory not found
- Ensure `data/arizona-us-senate-election-winner/` exists in the parent directory

### Error: Segment mapping file not found
- Ensure `all_users_analysis.csv` exists in the parent directory
- Run `segment_users.py` in the parent directory to generate segment mappings

### Error: Segment output directory not found (Step 3)
- Run Step 1 first to generate the segment positions

### No price data available
- The script will still generate graphs with investment-based odds only
- Check if price files exist in `data/arizona-us-senate-election-winner/prices/`

### Only 2-3 days in aggregated output
- This is **normal** if the market had concentrated trading activity
- Check the raw trade data to verify the actual trading period
- The pipeline accurately reflects when trades occurred

### Donation line not visible in graph
- Donation values are normalized (daily/total), so they may be very small
- Check the donation CSV files to see the actual normalized values
- The line should still appear, just at low values on the 0-1 scale

---

## Output Interpretation

### CSV Files
- `all_segments.csv`: Combined odds from all users
- `small_segment.csv`: Odds from Small segment users only
- `medium_segment.csv`: Odds from Medium segment users only
- `large_segment.csv`: Odds from Large segment users only

### Graphs

**Original Graph**:
- Compares price-based odds (blue) with investment-weighted odds from different user segments
- Shows how market prices compare to investment-weighted predictions
- Shows differences between small, medium, and large investors

**Donations Graph**:
- Shows normalized donation patterns over time
- Values represent proportion of total donations received each day
- Can identify donation spikes or patterns

**Combined Graph**:
- Shows all data together for comprehensive comparison
- Allows correlation analysis between donations and market behavior
- Useful for identifying relationships between donation activity and trading odds

---

## Notes

- Only processes `arizona-us-senate-election-winner` event
- All other events are ignored
- Outputs are stored in the `output/` folder within this directory
- Original files in the parent directory remain unchanged
- Donation data spans a longer period than trading data (donations go back to 2022-2023, trading is concentrated in Nov 2024)
