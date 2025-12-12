# Senate Market User Analysis - Documentation

## Overview

This analysis processes trading data from senate-related prediction markets to compute per-user statistics and segment users into Small, Medium, and Large categories based on trading volume.

## Data Processing Pipeline

### 1. Event Filtering
- **Input**: All event folders in `raw/` directory
- **Filter**: Keep only events with "senate" in folder name (case-insensitive)
- **Result**: 31 senate events retained, 47 non-senate events deleted

### 2. Per-Market User Statistics
For each market's trades CSV file:
- Group trades by `user_id` (proxyWallet)
- For each user in each market, calculate:
  - **total_buy**: Sum of `size × price` for all BUY trades
  - **total_sell**: Sum of `size × price` for all SELL trades
  - **net_amount**: `total_buy - total_sell`
  - **num_trades**: Count of all trades (BUY + SELL)

### 3. Global User Statistics
Aggregate across all markets for each unique user:
- **total_buy**: Sum of buy amounts across all markets
- **total_sell**: Sum of sell amounts across all markets
- **net_amount**: `total_buy - total_sell`
- **num_trades**: Sum of trades across all markets
- **num_markets**: Count of unique markets user traded in

### 4. User Segmentation
Users are segmented by total trading volume (`total_buy + total_sell`):
- **Small**: 0-50th percentile (bottom 50%)
- **Medium**: 50-90th percentile (middle 40%)
- **Large**: 90-100th percentile (top 10%)

## Metric Calculations

### Core Metrics

**total_buy**
- Formula: `Σ(size × price)` for all BUY trades
- Meaning: Total dollar amount spent on buying shares
- Example: User buys 10 shares at $0.50 each = $5.00 total_buy

**total_sell**
- Formula: `Σ(size × price)` for all SELL trades
- Meaning: Total dollar amount received from selling shares
- Example: User sells 5 shares at $0.60 each = $3.00 total_sell

**net_amount**
- Formula: `total_buy - total_sell`
- Meaning: Net position value
  - Positive: Net buyer (bought more than sold)
  - Negative: Net seller (sold more than bought)
  - Zero: Balanced trader

**total_volume**
- Formula: `total_buy + total_sell`
- Meaning: Total trading activity (both directions)
- Used for: Segmentation into Small/Medium/Large

**num_trades**
- Formula: Count of all trade records (BUY + SELL)
- Meaning: Total number of trading actions

**num_markets**
- Formula: Count of unique markets user traded in
- Meaning: Market diversity/engagement breadth

## Example Users and Scenarios

### Small Segment Examples

#### 1. Small Buyer (Single Trade)
```
User: 0x81f44533bc1a7bf4f6472fd3ad8099bbd7e7e80e
Segment: Small
total_buy: $15.00
total_sell: $0.00
net_amount: $15.00 (net buyer)
num_trades: 1
num_markets: 1
Scenario: One-time buyer, minimal engagement
```

#### 2. Small Balanced Trader
```
User: 0x0a866177667d708d0412bad213bc7c69d1c397e8
Segment: Small
total_buy: $2.80
total_sell: $2.72
net_amount: $0.08 (slightly net buyer)
num_trades: 2
num_markets: 1
Scenario: Small balanced trading, minimal net position
```

#### 3. Small Net Seller
```
User: 0x00a8fecdb131cbfc5ed4d23a08f6a1ce57c7ba13
Segment: Small
total_buy: $10.86
total_sell: $10.87
net_amount: -$0.01 (slightly net seller)
num_trades: 2
num_markets: 1
Scenario: Nearly balanced, slight net seller
```

### Medium Segment Examples

#### 4. Medium Buyer (Many Small Trades)
```
User: 0x5102f9546d6c0365a5d200abd4f7d07a6eec95ba
Segment: Medium
total_buy: $35,524.44
total_sell: $0.00
net_amount: $35,524.44 (strong net buyer)
num_trades: 9,990
num_markets: 1
Scenario: High-frequency buyer, many small trades, single market focus
```

#### 5. Medium Balanced Trader
```
User: 0x00735153971209e2d27b76aba35abfd96d531977
Segment: Medium
total_buy: $51.76
total_sell: $51.71
net_amount: $0.05 (nearly balanced)
num_trades: 2
num_markets: 1
Scenario: Balanced trading with minimal net exposure
```

#### 6. Medium Net Seller
```
User: 0x0015acce7275f3c3a08071521a41af7c4edc1a8a
Segment: Medium
total_buy: $1.47
total_sell: $1,809.83
net_amount: -$1,808.36 (strong net seller)
num_trades: 1,999
num_markets: 2
Scenario: Active seller across multiple markets, significant net short position
```

#### 7. Medium Multi-Market Trader
```
User: 0x000a0384e6ccedab80fbe870e86f9134d2b22572
Segment: Medium
total_buy: $63.90
total_sell: $0.00
net_amount: $63.90 (net buyer)
num_trades: 10
num_markets: 3
Scenario: Diversified across 3 markets, moderate activity
```

### Large Segment Examples

#### 8. Large Buyer (High Volume)
```
User: 0x965822b7b2d5bb4c3fdb9e5f24417c0bad086a49
Segment: Large
total_buy: $388,830.78
total_sell: $0.00
net_amount: $388,830.78 (strong net buyer)
num_trades: 1,998
num_markets: 1
Scenario: High-volume buyer, many trades, single market focus
```

#### 9. Large Buyer (Very High Volume)
```
User: 0x6f83329ddd430fb8f15da29e3d050e944ac8dc84
Segment: Large
total_buy: $1,166,492.34
total_sell: $0.00
net_amount: $1,166,492.34 (very strong net buyer)
num_trades: 5,994
num_markets: 1
Scenario: Ultra-high volume buyer, extremely active in single market
```

#### 10. Large Mixed Trader
```
User: 0x0d2be844127be9d2f7fb4da39283cce668c7c7b4
Segment: Large
total_buy: $567,332.20
total_sell: $94.34
net_amount: $567,237.87 (strong net buyer)
num_trades: 6,003
num_markets: 1
Scenario: High-volume trader with both buy and sell activity, primarily net buyer
```

## Key Insights from Examples

### Trading Patterns

1. **Pure Buyers**: Many users only buy (total_sell = 0), indicating they hold positions without selling
2. **Pure Sellers**: Fewer users only sell, typically exiting positions
3. **Balanced Traders**: Users with similar buy/sell amounts, indicating active trading
4. **Net Sellers**: Users who sell more than buy, may be profit-taking or exiting positions

### Market Engagement

1. **Single Market Focus**: Most users trade in 1 market (focused strategy)
2. **Multi-Market Diversification**: Some users trade across 2-3+ markets (diversified strategy)
3. **Trade Frequency**: Ranges from 1 trade to 14,000+ trades per user

### Segment Characteristics

- **Small Segment**: Low volume ($0-$50 typically), 1-5 trades, mostly single market
- **Medium Segment**: Moderate volume ($50-$400K), varied trade counts, some multi-market
- **Large Segment**: High volume ($400K+), many trades (1,000+), typically single market focus

## Output Files

1. **`output/combined/user_global_senate_stats.csv`**: Per-user statistics across all markets
2. **`segmentation_results/user_segments.csv`**: All users with segment assignments
3. **`segmentation_results/segment_statistics.csv`**: Aggregated statistics for each segment
4. **`segmentation_results/overall_summary.csv`**: Overall statistics and percentiles

## Usage

```bash
# Process senate markets and generate user statistics
python3 process_senate_analysis.py

# Generate user segments and statistics
python3 segment_analysis.py
```

## Notes

- All amounts are in USD
- Trades are aggregated across all senate markets
- Users are uniquely identified by their wallet address (proxyWallet)
- Segmentation is based on total trading volume, not net position

