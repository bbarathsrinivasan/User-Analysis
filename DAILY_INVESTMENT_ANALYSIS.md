# Daily User Investment Analysis

## Overview

This analysis processes trading data to create daily user investment files for each market, tracking user trading activity by day relative to the market end date. Each user's trading activity is aggregated by day, showing buy amounts, sell amounts, net positions, and trade counts.

## Methodology

### 1. Market End Date Determination

For each market, the end date is determined as follows:
- **Primary**: Use `market_endDate` from the meta CSV file if available
- **Fallback**: Use the maximum timestamp from trades (last trade date) if meta data is unavailable

### 2. Day Index Calculation

The `day_index` represents days relative to the market end date:
- **day_index = 0**: Market end day (resolution day)
- **day_index < 0**: Days before end (e.g., -5 = 5 days before end)
- **day_index > 0**: Should not exist (no trades after market end)

Formula: `day_index = (trade_date - market_end_date).days`

### 3. Daily Aggregation

For each user in each market, trades are grouped by `day_index` and the following metrics are calculated:

- **daily_buy**: Sum of `size × price` for all BUY trades on that day
- **daily_sell**: Sum of `size × price` for all SELL trades on that day
- **daily_net**: `daily_buy - daily_sell` (net position change for the day)
- **trade_count**: Number of trades executed on that day

Days with no trading activity are excluded from the output.

### 4. Output Structure

Files are organized as:
```
user_trades/
  {event_slug}/
    {market_slug}/
      {user_id}.csv
```

Each CSV file contains columns:
- `day_index`: Days relative to market end (0 = end day, negative = before end)
- `date`: Actual calendar date
- `daily_buy`: Total buy amount for the day
- `daily_sell`: Total sell amount for the day
- `daily_net`: Net amount (buy - sell) for the day
- `trade_count`: Number of trades on that day

## Example User Files

### Example 1: Active Multi-Day Trader (Arizona Senate Market)

**User**: `0x3e5630959499c5b5e55aceeeeae7446933d335d5`  
**Market**: `will-gallego-win-arizona-senate-election-by-1-2`  
**Event**: `arizona-senate-election-margin-of-victory`  
**Trading Days**: 14 days  
**Total Trades**: 135 trades  
**Day Range**: -38 to -22 (16 days before end)

This user shows active trading across multiple days with both buying and selling activity:

```csv
day_index,date,daily_buy,daily_sell,daily_net,trade_count
-38,2024-11-09,100.82,45.60,55.22,7
-37,2024-11-10,19.97,81.06,-61.09,25
-36,2024-11-11,10.08,1.67,8.41,13
-35,2024-11-12,70.34,118.08,-47.74,39
-34,2024-11-13,0.00,37.65,-37.65,18
-33,2024-11-14,0.00,4.51,-4.51,1
-32,2024-11-15,1.00,1.12,-0.12,7
-31,2024-11-16,0.01,0.05,-0.04,2
-30,2024-11-17,0.11,19.25,-19.14,14
-29,2024-11-18,0.00,1.95,-1.95,1
-28,2024-11-19,0.00,1.42,-1.42,1
-27,2024-11-20,0.00,1.06,-1.06,2
-24,2024-11-23,0.00,0.12,-0.12,2
-22,2024-11-25,4.41,0.00,4.41,3
```

**Analysis**: This user started as a net buyer (day -38), then became a net seller over subsequent days, indicating position adjustment or profit-taking behavior.

### Example 2: High-Volume Seller (Next Senate Majority Leader)

**User**: `0xf0b0ef1d6320c6be896b4c9c54dd74407e7f8cab`  
**Market**: `will-john-thune-be-the-next-seante-majority-leader`  
**Event**: `next-senate-majority-leader`  
**Trading Days**: 10 days  
**Total Trades**: 30,006 trades  
**Day Range**: -190 to -178 (12 days before end)

This user shows extremely high-volume selling activity:

```csv
day_index,date,daily_buy,daily_sell,daily_net,trade_count
-190,2024-12-22,0.00,67893.30,-67893.30,13986
-189,2024-12-23,0.00,1957.44,-1957.44,1998
-188,2024-12-24,0.00,28891.40,-28891.40,5994
-187,2024-12-25,0.00,43553.18,-43553.18,5994
-186,2024-12-26,0.00,10436.35,-10436.35,1998
-185,2024-12-27,0.00,101.25,-101.25,14
-184,2024-12-28,0.00,127.04,-127.04,13
-183,2024-12-29,0.00,53.27,-53.27,6
-179,2025-01-02,0.00,0.01,-0.01,1
-178,2025-01-03,0.00,0.28,-0.28,2
```

**Analysis**: This is a high-frequency trader with massive selling activity, executing thousands of trades per day. The user is consistently a net seller, indicating they're exiting positions or taking profits.

### Example 3: Sporadic Seller (Nebraska Special Election)

**User**: `0xf0b0ef1d6320c6be896b4c9c54dd74407e7f8cab`  
**Market**: `will-a-republican-win-nebraska-special-senate-election`  
**Event**: `nebraska-senate-special-election`  
**Trading Days**: 12 days  
**Total Trades**: 23 trades  
**Day Range**: -39 to -6 (33 days span)

This user shows sporadic selling activity over a long period:

```csv
day_index,date,daily_buy,daily_sell,daily_net,trade_count
-39,2024-09-27,0.00,29.91,-29.91,2
-38,2024-09-28,0.00,0.97,-0.97,1
-37,2024-09-29,0.00,0.85,-0.85,1
-36,2024-09-30,0.00,2.35,-2.35,4
-35,2024-10-01,0.00,0.62,-0.62,1
-34,2024-10-02,0.00,0.00,-0.00,1
-33,2024-10-03,0.00,0.13,-0.13,1
-32,2024-10-04,0.00,0.27,-0.27,1
-29,2024-10-07,0.00,2.55,-2.55,8
-16,2024-10-20,0.00,0.76,-0.76,1
-13,2024-10-23,0.00,1.62,-1.62,1
-6,2024-10-30,0.00,0.16,-0.16,1
```

**Analysis**: This user makes small, infrequent sell trades over a long time period, indicating a gradual exit strategy or position management approach.

### Example 4: Simple Two-Day Trader (Florida Senate)

**User**: `0xe9c6356f646d8b9b4b6715c7fac86bfd2395fbd3`  
**Market**: `will-the-democrats-win-the-florida-senate-race-in-2026`  
**Event**: `florida-senate-election-winner`  
**Trading Days**: 2 days  
**Total Trades**: 2 trades  
**Day Range**: -2 to 0 (end day)

A simple example showing buy and sell on different days:

```csv
day_index,date,daily_buy,daily_sell,daily_net,trade_count
-2,2025-10-21,1.70,0.00,1.70,1
0,2025-10-23,0.00,1.65,-1.65,1
```

**Analysis**: This user bought on day -2 and sold on the end day (day 0), a simple round-trip trade.

## Key Insights

### Trading Patterns

1. **Active Multi-Day Traders**: Users who trade consistently across multiple days, adjusting positions based on market conditions
2. **High-Frequency Traders**: Users executing thousands of trades per day, often with automated strategies
3. **Sporadic Traders**: Users making occasional trades over extended periods
4. **Simple Traders**: Users making one or two trades, typically buy-and-hold or quick round-trip

### Day Index Patterns

- Most trading activity occurs in the days leading up to market end (day_index close to 0)
- Early trading (large negative day_index) often indicates early position establishment
- End-day trading (day_index = 0) may indicate last-minute position adjustments or exits

### Net Position Analysis

- **Consistent Net Buyers**: Users accumulating positions over time
- **Consistent Net Sellers**: Users exiting positions or taking profits
- **Balanced Traders**: Users with mixed buy/sell activity, actively managing positions

## Statistics

- **Total Markets Processed**: 66
- **Total Users**: 6,158
- **Total Trades**: 9,008,053

## File Locations

All daily user investment files are located in:
```
user_trades/{event_slug}/{market_slug}/{user_id}.csv
```

## Usage

To regenerate the daily investment files:

```bash
python3 daily_user_investment.py
```

The script processes all senate markets and generates individual CSV files for each user in each market, showing their daily trading activity relative to the market end date.

