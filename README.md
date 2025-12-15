# Trade Data Pipeline - User Analysis

A Python data pipeline for processing trade data and performing per-user analysis across all markets and events.

## Overview

This pipeline processes trade data stored as CSV files, computes daily aggregations per user per market, and generates two types of output:

1. **Per-Market Output**: Individual analysis files for each user in each market
2. **All Markets Output**: Aggregated analysis files combining all markets for each user

## Requirements

- Python 3.8+
- pandas >= 2.0.0

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Data Structure

The pipeline expects trade data in the following directory structure:

```
raw/
  └── <event_id>/
      └── trades/
          └── <market_slug>_trades.csv
```

Each CSV file should contain the following columns:
- `proxyWallet` (user_id)
- `side` (BUY/SELL)
- `size` (quantity)
- `timestamp` (unix timestamp)
- `slug` (market_slug)
- `eventSlug` (event_id)
- `outcome` (Yes/No - token type)

## Usage

Run the pipeline:

```bash
python pipeline.py
```

The pipeline will:
1. Discover all events and markets automatically
2. Process each market sequentially (memory-safe)
3. Generate per-market output files
4. Generate aggregated all-markets output files

## Output Structure

### 1. Per-Market Output

Location: `output/user_<user_id>/event_<event_id>/market_<market_id>/`

For each user in each market, two CSV files are generated:
- `yes_token.csv` - YES token trades
- `no_token.csv` - NO token trades

**Example: Per-Market Output**

File: `output/user_0x1fd0b45ad25e1ed781e21a192164fd01d775e7ed/event_will-fischer-win-nebraska-senate-election-by-7-points/market_will-fischer-win-nebraska-senate-election-by-7-points/yes_token.csv`

```csv
event_id,market_id,market_slug,user_id,day_offset,daily_buy,daily_sell,net_tokens,cumulative_position
will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,0x1fd0b45ad25e1ed781e21a192164fd01d775e7ed,-25,2.38095,0.0,2.38095,2.38095
will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,0x1fd0b45ad25e1ed781e21a192164fd01d775e7ed,-24,0.0,0.0,0.0,2.38095
will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,0x1fd0b45ad25e1ed781e21a192164fd01d775e7ed,-23,0.0,0.0,0.0,2.38095
will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,0x1fd0b45ad25e1ed781e21a192164fd01d775e7ed,-22,0.0,2.38,-2.38,0.00095
will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,0x1fd0b45ad25e1ed781e21a192164fd01d775e7ed,-21,0.0,0.0,0.0,0.00095
...
will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,will-fischer-win-nebraska-senate-election-by-7-points,0x1fd0b45ad25e1ed781e21a192164fd01d775e7ed,0,0.0,0.0,0.0,0.00095
```

**Interpretation:**
- This user bought 2.38095 YES tokens on day -25 (25 days before the last trading day)
- On day -22, they sold 2.38 tokens, resulting in a net position of 0.00095 tokens
- The cumulative_position shows the running total, which remains at 0.00095 for all subsequent days with no trades
- Day 0 represents the last trading day in this market

### 2. All Markets Output

Location: `all_markets_output/user_<user_id>/`

For each user, two CSV files are generated combining all markets:
- `yes_token.csv` - All YES token trades across all markets
- `no_token.csv` - All NO token trades across all markets

**Example: All Markets Output (Multiple Markets)**

File: `all_markets_output/user_0x08325309c56e74516a35dd87c86fb9d25db806a6/yes_token.csv`

```csv
event_id,market_id,market_slug,user_id,day_offset,daily_buy,daily_sell,net_tokens,cumulative_position
arizona-senate-election-margin-of-victory,will-kari-lake-win-arizona-senate-election-by-2-or-more,will-kari-lake-win-arizona-senate-election-by-2-or-more,0x08325309c56e74516a35dd87c86fb9d25db806a6,-4,20.0,0.0,20.0,20.0
arizona-senate-election-margin-of-victory,will-kari-lake-win-arizona-senate-election-by-2-or-more,will-kari-lake-win-arizona-senate-election-by-2-or-more,0x08325309c56e74516a35dd87c86fb9d25db806a6,-3,0.0,0.0,0.0,20.0
arizona-senate-election-margin-of-victory,will-kari-lake-win-arizona-senate-election-by-2-or-more,will-kari-lake-win-arizona-senate-election-by-2-or-more,0x08325309c56e74516a35dd87c86fb9d25db806a6,-2,0.0,0.0,0.0,20.0
arizona-senate-election-margin-of-victory,will-kari-lake-win-arizona-senate-election-by-2-or-more,will-kari-lake-win-arizona-senate-election-by-2-or-more,0x08325309c56e74516a35dd87c86fb9d25db806a6,-1,0.0,0.0,0.0,20.0
arizona-senate-election-margin-of-victory,will-kari-lake-win-arizona-senate-election-by-1-2,will-kari-lake-win-arizona-senate-election-by-1-2,0x08325309c56e74516a35dd87c86fb9d25db806a6,0,20.0,0.0,20.0,40.0
arizona-senate-election-margin-of-victory,will-kari-lake-win-arizona-senate-election-by-2-or-more,will-kari-lake-win-arizona-senate-election-by-2-or-more,0x08325309c56e74516a35dd87c86fb9d25db806a6,0,0.0,0.0,0.0,40.0
```

**Interpretation:**
- This user traded in 2 different markets within the same event
- First trade: 20.0 YES tokens in market "will-kari-lake-win-arizona-senate-election-by-2-or-more" on day -4 (cumulative: 20.0)
- Second trade: 20.0 YES tokens in market "will-kari-lake-win-arizona-senate-election-by-1-2" on day 0 (cumulative: 40.0)
- The cumulative_position is a **global running total** across all markets and all events, calculated chronologically by day_offset
- Data is sorted by day_offset first, then by market_id (not event_id), so all markets from all events with the same day_offset are grouped together
- The event_id and market_id columns allow you to track which event and market each trade came from

**Example: All Markets Output (Single Market)**

File: `all_markets_output/user_0x1bf34b8800f4a942bbfa0d47ba06c046b4bffc7e/yes_token.csv`

```csv
event_id,market_id,market_slug,user_id,day_offset,daily_buy,daily_sell,net_tokens,cumulative_position
arizona-senate-election-margin-of-victory,will-gallego-win-arizona-senate-election-by-2-3-or-more,will-gallego-win-arizona-senate-election-by-2-3-or-more,0x1bf34b8800f4a942bbfa0d47ba06c046b4bffc7e,-8,99.636062,0.0,99.636062,99.636062
arizona-senate-election-margin-of-victory,will-gallego-win-arizona-senate-election-by-2-3-or-more,will-gallego-win-arizona-senate-election-by-2-3-or-more,0x1bf34b8800f4a942bbfa0d47ba06c046b4bffc7e,-7,0.0,0.0,0.0,99.636062
arizona-senate-election-margin-of-victory,will-gallego-win-arizona-senate-election-by-2-3-or-more,will-gallego-win-arizona-senate-election-by-2-3-or-more,0x1bf34b8800f4a942bbfa0d47ba06c046b4bffc7e,-6,0.0,0.0,0.0,99.636062
...
arizona-senate-election-margin-of-victory,will-gallego-win-arizona-senate-election-by-2-3-or-more,will-gallego-win-arizona-senate-election-by-2-3-or-more,0x1bf34b8800f4a942bbfa0d47ba06c046b4bffc7e,0,0.0,0.0,0.0,99.636062
```

**Interpretation:**
- This user only traded in one market
- They bought 99.636062 YES tokens on day -8
- No subsequent trades, so cumulative_position remains constant at 99.636062

## Column Descriptions

All output files contain the following columns:

- **event_id**: The event identifier (e.g., "arizona-senate-election-margin-of-victory")
- **market_id**: The market identifier (same as market_slug)
- **market_slug**: Human-readable market identifier
- **user_id**: User wallet address (proxyWallet from input)
- **day_offset**: Days relative to the last trading day in that market
  - `0` = last trading day
  - `-1` = one day before last trading day
  - `-2` = two days before last trading day
  - etc.
- **daily_buy**: Sum of all BUY quantities for that day
- **daily_sell**: Sum of all SELL quantities for that day
- **net_tokens**: daily_buy - daily_sell
- **cumulative_position**: Running cumulative sum of net_tokens
  - In per-market output: cumulative within that market
  - In all-markets output: global cumulative across all markets

## Key Features

1. **Day Offset Calculation**: The last trading day in each market is normalized to day 0, with previous days as -1, -2, etc.

2. **Missing Days Filled**: Days with no trades are filled with zeros for daily_buy and daily_sell, while cumulative_position carries forward.

3. **Market-by-Market Processing**: Data is processed sequentially to remain memory-safe for large datasets.

4. **Vectorized Operations**: Uses efficient pandas groupby and aggregation operations.

5. **Global Cumulative Position**: In all-markets output, cumulative_position is a global running total across all markets and all events, calculated chronologically by sorting first by day_offset, then by market_id (not event_id). This ensures all markets from all events with the same day_offset are grouped together, and the cumulative position reflects true date-based progression across all markets and events.

## Notes

- Each market belongs to only one event
- Price information is ignored; only quantity matters
- Token types are normalized to YES/NO (from Yes/No in input)
- Output directories are created automatically if they don't exist

## File Structure

```
.
├── pipeline.py          # Main pipeline script
├── utils.py             # Helper functions
├── requirements.txt     # Dependencies
├── README.md           # This file
├── raw/                # Input data directory
│   └── <event_id>/
│       └── trades/
│           └── *.csv
├── output/             # Per-market output
│   └── user_<user_id>/
│       └── event_<event_id>/
│           └── market_<market_id>/
│               ├── yes_token.csv
│               └── no_token.csv
└── all_markets_output/ # Aggregated output
    └── user_<user_id>/
        ├── yes_token.csv
        └── no_token.csv
```
