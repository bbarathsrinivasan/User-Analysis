# Data Segment Pipeline - Quick Reference Prompt

## Task Description

Create a pipeline that processes market trade data and generates segment-based aggregation files with comparison graphs showing investment-based odds vs. price-based market odds.

## Pipeline Overview

**Two-step process:**

1. **Step 1**: Process raw trades → Create per-user position files
2. **Step 2**: Aggregate by segment → Generate CSV files and comparison graphs

---

## Step 1: Build Segment Positions

**Script**: `build_segment_positions_data.py`

**Input**: 
- `data/<event_id>/trades/<market_slug>_trades.csv`
- `data/<event_id>/prices/<market_slug>_price.csv` (optional)

**Process**:
1. Load trades, map columns (proxyWallet→user_id, outcome→token_type)
2. Compute day_offset: closing date = 0, earlier days negative
3. Aggregate daily trades per (user_id, token_type, day_offset)
4. Calculate cumulative positions and individual positions
5. Load daily prices (if available)

**Output**: 
- `data_segment_output/<event_id>/<market_slug>/user_<user_id>.csv`

**Key Calculations**:
- `yes_cumulative_position` = cumulative sum of yes_net_tokens
- `no_cumulative_position` = cumulative sum of no_net_tokens
- `individual_yes_position` = H_y (if >0) + (-H_n) (if <0)
- `individual_no_position` = H_n (if >0) + (-H_y) (if <0)

---

## Step 2: Build Segment Aggregation

**Script**: `build_segment_aggregation_data.py`

**Input**:
- `data_segment_output/` (from Step 1)
- `all_users_analysis.csv` (user_id → segment mapping)
- `data/<event_id>/prices/` (for market odds)

**Segment Thresholds** (based on `cumulative_total_value_max`):
- **Large**: ≥ 1,000,000
- **Medium**: 10,000 ≤ x < 1,000,000
- **Small**: < 10,000

**Process**:
1. Load segment mapping (Small/Medium/Large)
2. For each market, aggregate positions by segment:
   - `agg_yes` = sum(individual_yes_position) where yes_cumulative_position != 0
   - `agg_no` = sum(individual_no_position) where no_cumulative_position != 0
   - `odds` = agg_yes / (agg_yes + agg_no)
3. Load price odds: Get end-of-day YES prices, convert to day_offset
4. Create 5-line comparison graph

**Output**:
- `data_segment/<event_id>/<market_slug>/all_segments.csv`
- `data_segment/<event_id>/<market_slug>/small_segment.csv`
- `data_segment/<event_id>/<market_slug>/medium_segment.csv`
- `data_segment/<event_id>/<market_slug>/large_segment.csv`
- `data_segment/<event_id>/<market_slug>/odds_comparison.png`

**Graph Lines** (5 total):
1. Price-based Market Odds (blue) - End-of-day YES prices
2. All Segments (green) - Investment-based odds
3. Small Segment (orange) - Investment-based odds
4. Medium Segment (red) - Investment-based odds
5. Large Segment (purple) - Investment-based odds

---

## Key Requirements

### Data Formats

**Trade CSV** (`*_trades.csv`):
- Columns: `proxyWallet`, `side`, `size`, `timestamp`, `slug`, `eventSlug`, `outcome`
- Map: `proxyWallet`→`user_id`, `outcome`→`token_type` (YES/NO)

**Price CSV** (two formats supported):
- Format 1: `*_price.csv` with `timestamp`, `token_id`, `price`
- Format 2: `*_closing_prices.csv` with `date`, `token_type`, `price`

### Day Offset Calculation
```
closing_date = max(date) in market
day_offset = (date - closing_date).days
```
- Closing day = 0
- Earlier days = negative

### Price Loading for Market Odds
- Get end-of-day price for each date (last price by timestamp)
- Filter YES token prices only
- Convert dates to day_offset
- Filter day_offset <= 0 (up to closing date)

### Segment Aggregation
- Group users by segment (Small/Medium/Large)
- Aggregate `individual_yes_position` and `individual_no_position`
- Only include users with non-zero cumulative positions
- Calculate odds: `agg_yes / (agg_yes + agg_no)`

---

## Prerequisites

**Before running the segment pipeline**, generate user segments:

```bash
# Step 0a: Generate user statistics (requires date_group_token.csv files from main pipeline)
python analyze_all_users.py

# Step 0b: Classify users into segments
python segment_users.py
```

This creates/updates `all_users_analysis.csv` with `user_segment` column based on:
- **Large**: `cumulative_total_value_max` ≥ 1,000,000
- **Medium**: 10,000 ≤ x < 1,000,000
- **Small**: < 10,000

## Execution

```bash
# Step 1: Process trades
python build_segment_positions_data.py

# Step 2: Generate segment aggregations and graphs
python build_segment_aggregation_data.py
```

---

## Output Structure

```
data_segment_output/          # Step 1 output
├── <event_id>/
│   └── <market_slug>/
│       └── user_*.csv

data_segment/                 # Step 2 output
├── <event_id>/
│   └── <market_slug>/
│       ├── all_segments.csv
│       ├── small_segment.csv
│       ├── medium_segment.csv
│       ├── large_segment.csv
│       └── odds_comparison.png
```

---

## Critical Implementation Details

1. **Individual Position Formula**:
   ```
   H_y = yes_cumulative_position
   H_n = no_cumulative_position
   individual_yes_position = (H_y if H_y > 0 else 0) + (-H_n if H_n < 0 else 0)
   individual_no_position = (H_n if H_n > 0 else 0) + (-H_y if H_y < 0 else 0)
   ```

2. **Price Loading**:
   - For `*_price.csv`: Map token_id→token_type using trades file
   - Get last price per day (by timestamp)
   - Convert to day_offset using market closing date

3. **Segment Filtering**:
   - Only aggregate users with segment mapping
   - Only include positions where cumulative_position != 0

4. **Graph Requirements**:
   - 5 lines total (1 price-based + 4 investment-based)
   - X-axis: day_offset (0 = closing day)
   - Y-axis: odds (0 to 1)
   - Different colors and markers for each line

---

## Dependencies

- pandas >= 2.0.0
- matplotlib
- numpy

## Required Files

- `data/` folder with market data
- `all_users_analysis.csv` with `user_id` and `user_segment` columns

**Generating Segment Mappings**:
1. Run `analyze_all_users.py` to create `all_users_analysis.csv` with user statistics
2. Run `segment_users.py` to classify users into segments based on `cumulative_total_value_max`:
   - Large: ≥ 1,000,000
   - Medium: 10,000 ≤ x < 1,000,000
   - Small: < 10,000

