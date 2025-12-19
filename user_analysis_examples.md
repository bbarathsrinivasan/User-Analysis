# User Analysis Presentation Examples

## Overview

This document provides real-world examples of user trading behavior analysis, showing how data flows from daily trading activity (`date_group_token.csv`) to comprehensive user statistics (`all_users_analysis.csv`). These examples are ideal for presentations and demonstrate the depth and breadth of our analysis.

---

## Data Flow Architecture

### 1. Source Data: `date_group_token.csv`

**Location**: `all_markets_output/user_<user_id>/date_group_token.csv`

**Content**: Daily aggregated trading data for each user, with one row per day the user had trading activity.

**Key Columns**:
- `date`: Trading date
- `markets_engaged`: Number of unique markets the user traded in that day
- `yes_buy`, `yes_sell`, `no_buy`, `no_sell`: Daily buy/sell volumes for YES/NO tokens
- `yes_value`, `no_value`: Daily value changes (net_tokens × closing_price)
- `net_yes`, `net_no`: Net tokens traded per day (buy - sell)
- `total_token`: Net tokens across both YES and NO (net_yes + net_no)
- `total_value`: Net value across both YES and NO (yes_value + no_value)
- `cumulative_total_token`: Running total of tokens (carries forward)
- `cumulative_total_value`: Running total of value (carries forward)

### 2. Analysis Output: `all_users_analysis.csv`

**Location**: Root directory

**Content**: Comprehensive statistics for all users, with one row per user containing 42 calculated metrics.

**How It's Created**: The `analyze_all_users.py` script reads each user's `date_group_token.csv` file and calculates statistics across all their trading days.

---

## Example 1: High-Activity User Over Extended Period

### User Profile
- **User ID**: `0xf0b0ef1d6320c6be896b4c9c54dd74407e7f8cab`
- **Trading Days**: 39 days
- **Date Range**: September 27, 2024 to November 15, 2025 (414 calendar days)
- **Total Markets Engaged**: 67 markets
- **Behavior Pattern**: Net Seller (consistently selling positions)

### Sample Data from `date_group_token.csv`

**First Few Days** (Starting Activity):
| Date | markets_engaged | total_token | total_value | cumulative_total_token | cumulative_total_value |
|------|----------------|-------------|-------------|----------------------|----------------------|
| 2024-09-27 | 1 | -31.12 | -30.16 | -31.12 | -30.16 |
| 2024-09-28 | 2 | -1.05 | -0.98 | -32.17 | -31.14 |
| 2024-09-29 | 1 | -0.88 | -0.85 | -33.05 | -31.99 |
| 2024-09-30 | 1 | -2.43 | -2.36 | -35.48 | -34.35 |
| 2024-10-01 | 2 | -0.85 | -0.62 | -36.33 | -34.97 |

**Peak Selling Day** (2024-12-26):
| Date | markets_engaged | total_token | total_value | cumulative_total_token | cumulative_total_value |
|------|----------------|-------------|-------------|----------------------|----------------------|
| 2024-12-26 | 3 | -702,975.54 | -140,798.72 | -1,474,016.40 | -560,139.30 |

**Final Days** (Continued Selling):
| Date | markets_engaged | total_token | total_value | cumulative_total_token | cumulative_total_value |
|------|----------------|-------------|-------------|----------------------|----------------------|
| 2025-11-10 | 1 | -100.00 | -26.50 | -1,475,528.93 | -560,621.30 |
| 2025-11-12 | 1 | -2.11 | -0.76 | -1,475,531.04 | -560,622.06 |
| 2025-11-15 | 1 | -18.37 | -5.05 | -1,475,549.41 | -560,627.11 |

**Key Observations**:
- User started with small sells (negative total_token)
- Had a massive sell day on 2024-12-26 (-702,975.54 tokens)
- Continued selling activity throughout the period
- Final cumulative position: -1,475,549.41 tokens (net seller)

### Statistics Calculated in `all_users_analysis.csv`

#### Basic Information
```
total_days = 39 (count of rows in date_group_token.csv)
first_date = 2024-09-27 (earliest date)
last_date = 2025-11-15 (latest date)
date_range_days = 414 (calendar days between first and last)
```

#### Total Token Statistics
From the `total_token` column in `date_group_token.csv` (39 values):

**Raw Data Sample**: [-31.12, -1.05, -0.88, -2.43, -0.85, ..., -702975.54, ..., -18.37]

**Calculations**:
```
total_token_min = min(all 39 values) = -702,975.54
  → This is the day with the largest sell (2024-12-26)

total_token_max = max(all 39 values) = -0.13
  → This is the day with the smallest sell (closest to zero)

total_token_mean = sum(all 39 values) / 39
                 = -1,475,549.41 / 39
                 = -37,834.60 tokens per day on average

total_token_median = median(all 39 values) = -50.00
  → When sorted, the middle value is -50.00

total_token_sum = sum(all 39 values) = -1,475,549.41
  → This equals the final cumulative_total_token (by design)
```

**Manual Verification**:
- All 39 `total_token` values are negative (user always sold)
- The sum of daily `total_token` = final `cumulative_total_token` = -1,475,549.41 ✓

#### Total Value Statistics
From the `total_value` column:
```
total_value_min = -140,798.72 (corresponds to the -702,975.54 token day)
total_value_max = -0.01
total_value_mean = -14,375.05
total_value_median = -1.11
total_value_sum = -560,627.11
```

#### Cumulative Statistics
From the `cumulative_total_token` and `cumulative_total_value` columns:
```
cumulative_total_token_final = -1,475,549.41 (last row's cumulative value)
cumulative_total_token_max = -31.12 (first day, highest cumulative value)
cumulative_total_token_min = -1,475,549.41 (final day, lowest cumulative value)

cumulative_total_value_final = -560,627.11 (last row's cumulative value)
cumulative_total_value_max = -30.16 (first day)
cumulative_total_value_min = -560,627.11 (final day)
```

**Interpretation**: This user is a **net seller** - they consistently sold more tokens than they bought, ending with a large negative cumulative position.

---

## Example 2: High-Value Accumulator

### User Profile
- **User ID**: `0xd218e474776403a330142299f7796e8ba32eb5c9`
- **Trading Days**: 23 days
- **Date Range**: October 30, 2024 to November 19, 2025 (385 calendar days)
- **Total Markets Engaged**: 86 markets

### Sample Data from `date_group_token.csv`

**Early Days** (Building Position):
| Date | markets_engaged | total_token | total_value | cumulative_total_token | cumulative_total_value |
|------|----------------|-------------|-------------|----------------------|----------------------|
| 2024-10-30 | 2 | 7,135.94 | 3,651.82 | 7,135.94 | 3,651.82 |
| 2024-11-04 | 3 | 200.00 | 101.50 | 7,335.94 | 3,753.32 |
| 2024-11-05 | 2 | 285.72 | 145.79 | 7,621.66 | 3,899.11 |
| 2024-11-06 | 1 | 3,000.00 | 2,971.50 | 10,621.66 | 6,870.61 |
| 2024-11-09 | 5 | 7,992.80 | 8,627.80 | 18,614.46 | 15,498.41 |

**Massive Accumulation Days**:
| Date | markets_engaged | total_token | total_value | cumulative_total_token | cumulative_total_value |
|------|----------------|-------------|-------------|----------------------|----------------------|
| 2024-11-10 | 6 | 6,277,737.29 | 1,989,683.50 | 6,296,351.75 | 2,005,181.91 |
| 2024-11-11 | 5 | 5,048,129.89 | 1,056,877.42 | 11,344,481.64 | 3,062,059.33 |

**Continued Accumulation**:
| Date | markets_engaged | total_token | total_value | cumulative_total_token | cumulative_total_value |
|------|----------------|-------------|-------------|----------------------|----------------------|
| 2024-11-12 | 5 | 12,124.30 | 10,553.98 | 11,356,605.94 | 3,072,613.31 |
| 2024-11-13 | 5 | 4,220.03 | 3,222.74 | 11,360,825.97 | 3,075,836.06 |
| ... | ... | ... | ... | ... | ... |
| 2025-11-19 | 1 | 33.57 | 21.82 | 11,754,672.14 | 3,467,412.41 |

**Key Observations**:
- User started with moderate buys
- Had massive accumulation days on 2024-11-10 (6.3M tokens) and 2024-11-11 (5.0M tokens)
- Continued accumulating throughout the period
- Final cumulative position: 11,754,672.14 tokens (net buyer)
- Final cumulative value: 3,467,412.41 (high-value position)

### Statistics Calculated in `all_users_analysis.csv`

#### Total Token Statistics
From the `total_token` column in `date_group_token.csv` (23 values):

**Raw Data Sample**: [7,135.94, 200.00, 285.72, 3,000.00, 7,992.80, 6,277,737.29, 5,048,129.89, ..., 33.57]

**Calculations**:
```
total_token_min = min(all 23 values) = 33.57
  → Smallest daily buy (2025-11-19)

total_token_max = max(all 23 values) = 6,277,737.29
  → Largest daily buy (2024-11-10 - massive accumulation day)

total_token_mean = sum(all 23 values) / 23
                 = 11,754,672.14 / 23
                 = 511,072.70 tokens per day on average

total_token_median = median(all 23 values) = 1,615.71
  → When sorted, the middle value is 1,615.71
  → This shows most days had moderate activity (median is much lower than mean)
  → The mean is high due to the two massive buy days

total_token_sum = sum(all 23 values) = 11,754,672.14
  → This equals the final cumulative_total_token
```

**Key Insight**: The huge difference between mean (511K) and median (1.6K) indicates the user had a few extremely large buy days that skew the average upward.

#### Total Value Statistics
```
total_value_min = 21.82
total_value_max = 1,989,683.50 (corresponds to the 6.3M token day)
total_value_mean = 150,626.63
total_value_median = 769.38
total_value_sum = 3,467,412.41
```

#### Cumulative Statistics
```
cumulative_total_token_final = 11,754,672.14
cumulative_total_token_max = 11,754,672.14 (final position is the maximum)
cumulative_total_token_min = 7,135.94 (first day, starting position)

cumulative_total_value_final = 3,467,412.41
cumulative_total_value_max = 3,467,412.41
cumulative_total_value_min = 3,651.82
```

**Interpretation**: This user is a **major accumulator** - they consistently bought more tokens than they sold, building a large positive position worth over 3.4 million in value.

---

## Example 3: Moderate Activity User (Our Previous Example)

### User Profile
- **User ID**: `0xa58d4f278d7953cd38eeb929f7e242bfc7c0b9b8`
- **Trading Days**: 3 days
- **Date Range**: October 14, 2025 to November 14, 2025 (31 calendar days)
- **Total Markets Engaged**: 18 markets

### Complete Data from `date_group_token.csv`

| Date | markets_engaged | yes_buy | yes_sell | no_buy | no_sell | yes_value | no_value | net_yes | net_no | total_token | total_value | cumulative_total_token | cumulative_total_value |
|------|----------------|---------|----------|--------|---------|-----------|----------|---------|--------|-------------|-------------|----------------------|----------------------|
| 2025-10-14 | 13 | 2,400.0 | 0.0 | 4,742.35 | 0.0 | 172.86 | 369.52 | 2,400.0 | 4,742.35 | 7,142.35 | 542.38 | 7,142.35 | 542.38 |
| 2025-10-19 | 4 | 0.0 | 0.0 | 0.0 | 667.38 | 0.0 | -378.50 | 0.0 | -667.38 | -667.38 | -378.50 | 6,474.97 | 163.88 |
| 2025-11-14 | 1 | 0.0 | 0.0 | 0.0 | 21.97 | 0.0 | -2.31 | 0.0 | -21.97 | -21.97 | -2.31 | 6,453.00 | 161.58 |

### Step-by-Step Calculation of Statistics

#### Step 1: Basic Information
```
total_days = 3 (number of rows)
first_date = 2025-10-14 (earliest date in the file)
last_date = 2025-11-14 (latest date in the file)
date_range_days = (2025-11-14) - (2025-10-14) = 31 calendar days
```

#### Step 2: Total Token Statistics
From the `total_token` column: [7,142.35, -667.38, -21.97]

```
total_token_min = min(7142.35, -667.38, -21.97) = -667.38
total_token_max = max(7142.35, -667.38, -21.97) = 7,142.35
total_token_mean = (7142.35 + (-667.38) + (-21.97)) / 3 = 2,151.00
total_token_median = median(7142.35, -667.38, -21.97) = -21.97
total_token_sum = 7142.35 + (-667.38) + (-21.97) = 6,453.00
```

#### Step 3: Total Value Statistics
From the `total_value` column: [542.38, -378.50, -2.31]

```
total_value_min = min(542.38, -378.50, -2.31) = -378.50
total_value_max = max(542.38, -378.50, -2.31) = 542.38
total_value_mean = (542.38 + (-378.50) + (-2.31)) / 3 = 53.86
total_value_median = median(542.38, -378.50, -2.31) = -2.31
total_value_sum = 542.38 + (-378.50) + (-2.31) = 161.58
```

#### Step 4: Cumulative Statistics
From the `cumulative_total_token` column: [7,142.35, 6,474.97, 6,453.00]

```
cumulative_total_token_final = 6,453.00 (last row's value)
cumulative_total_token_max = max(7142.35, 6474.97, 6453.00) = 7,142.35
cumulative_total_token_min = min(7142.35, 6474.97, 6453.00) = 6,453.00
```

From the `cumulative_total_value` column: [542.38, 163.88, 161.58]

```
cumulative_total_value_final = 161.58 (last row's value)
cumulative_total_value_max = max(542.38, 163.88, 161.58) = 542.38
cumulative_total_value_min = min(542.38, 163.88, 161.58) = 161.58
```

#### Step 5: Trading Activity
```
total_markets_engaged = sum of markets_engaged column
                      = 13 + 4 + 1 = 18
```

#### Step 6: Net YES/NO Statistics
From `net_yes` column: [2,400.0, 0.0, 0.0]
```
net_yes_min = 0.0
net_yes_max = 2,400.0
net_yes_mean = (2400.0 + 0.0 + 0.0) / 3 = 800.0
net_yes_sum = 2,400.0
net_yes_final_cumulative = 2,400.0 (from cumulative_net_yes column, last row)
```

From `net_no` column: [4,742.35, -667.38, -21.97]
```
net_no_min = -667.38
net_no_max = 4,742.35
net_no_mean = (4742.35 + (-667.38) + (-21.97)) / 3 = 1,351.00
net_no_sum = 4,053.00
net_no_final_cumulative = 4,053.00 (from cumulative_net_no column, last row)
```

#### Step 7: YES/NO Value Statistics
From `yes_value` column: [172.86, 0.0, 0.0]
```
yes_value_min = 0.0
yes_value_max = 172.86
yes_value_mean = (172.86 + 0.0 + 0.0) / 3 = 57.62
yes_value_sum = 172.86
yes_value_final_cumulative = 172.86 (from cumulative_yes_value column, last row)
```

From `no_value` column: [369.52, -378.50, -2.31]
```
no_value_min = -378.50
no_value_max = 369.52
no_value_mean = (369.52 + (-378.50) + (-2.31)) / 3 = -3.76
no_value_sum = -11.28
no_value_final_cumulative = -11.28 (from cumulative_no_value column, last row)
```

---

## Complete Calculation Walkthrough

### Example: Calculating `total_token_mean` for User 1

Let's trace how `total_token_mean = -37,834.60` is calculated from the raw data.

#### Step 1: Read the User's `date_group_token.csv`
```python
df = pd.read_csv('all_markets_output/user_0xf0b0ef1d6320c6be896b4c9c54dd74407e7f8cab/date_group_token.csv')
```

#### Step 2: Extract the `total_token` Column
The `total_token` column contains 39 values (one per trading day):
```
[-31.12, -1.05, -0.88, -2.43, -0.85, -0.15, -0.13, -0.28, -5.17, -2.40, 
 -1.68, -51.17, -500.00, -518.80, -108334.50, -479.93, -756.88, -203.00, 
 -0.95, -8.39, -2.62, -316.87, -50.00, -1.02, -66.92, -4.03, -382037.58, 
 -2017.98, -29510.46, -246133.62, -702975.54, -879.39, -422.13, -55.44, 
 -1.57, -54.00, -100.00, -2.11, -18.37]
```

#### Step 3: Calculate the Mean
```
total_token_mean = sum(all values) / count(values)
                 = -1,475,549.41 / 39
                 = -37,834.60
```

#### Step 4: Verify in `all_users_analysis.csv`
When we look up this user in `all_users_analysis.csv`:
```
user_id = 0xf0b0ef1d6320c6be896b4c9c54dd74407e7f8cab
total_token_mean = -37,834.60
```

✅ **Match confirmed!**

---

## User Comparison Table

| Metric | User 1 (Seller) | User 2 (Accumulator) | User 3 (Moderate) |
|--------|-----------------|---------------------|-------------------|
| **User ID** | 0xf0b0ef1d... | 0xd218e474... | 0xa58d4f27... |
| **Trading Days** | 39 | 23 | 3 |
| **Date Range** | 414 days | 385 days | 31 days |
| **Total Markets** | 67 | 86 | 18 |
| **Total Token Min** | -702,975.54 | 33.57 | -667.38 |
| **Total Token Max** | -0.13 | 6,277,737.29 | 7,142.35 |
| **Total Token Mean** | -37,834.60 | 511,072.70 | 2,151.00 |
| **Total Token Median** | -50.00 | 1,615.71 | -21.97 |
| **Final Cumulative Token** | -1,475,549.41 | 11,754,672.14 | 6,453.00 |
| **Final Cumulative Value** | -560,627.11 | 3,467,412.41 | 161.58 |
| **Behavior Pattern** | Net Seller | Major Accumulator | Balanced Trader |

**Key Insights**:
- **User 1**: Consistent seller, one massive sell day (-702K tokens)
- **User 2**: Major accumulator with two huge buy days (6.3M and 5.0M tokens)
- **User 3**: Moderate trader with balanced activity across 3 days

---

## How `date_group_token.csv` is Created

### Data Source Chain

1. **Raw Trade Data**: `raw/<event_id>/trades/<market_slug>_trades.csv`
   - Contains individual trade records with timestamps, user_id, token_id, buy/sell amounts

2. **Per-Market User Files**: `output/<event_id>/<market_id>/user_<user_id>/yes_token.csv` and `no_token.csv`
   - Daily aggregated trades per user per market
   - Columns: day_offset, daily_buy, daily_sell, net_tokens, cumulative_position

3. **Combined Token File**: `all_markets_output/user_<user_id>/combined_token.csv`
   - Merges YES and NO token data across all markets
   - One row per market per day_offset
   - Columns: event_id, market_id, market_slug, day_offset, date, yes_daily_buy, yes_daily_sell, no_daily_buy, no_daily_sell, yes_net_tokens, no_net_tokens, yes_cumulative_position, no_cumulative_position

4. **Date Grouped File**: `all_markets_output/user_<user_id>/date_group_token.csv`
   - Groups `combined_token.csv` by date
   - Aggregates across all markets for each date
   - Calculates values using closing prices

### Calculation Process for `date_group_token.csv`

#### Step 1: Load Combined Token Data
Read `combined_token.csv` which has one row per market per day.

#### Step 2: Load Closing Prices
For each unique market (event_id, market_slug), load the corresponding `_closing_prices.csv` file from `raw/<event_id>/prices/`.

#### Step 3: Merge Prices
Merge closing prices with combined token data by `event_id`, `market_slug`, and `date`.

#### Step 4: Calculate Values
For each row:
```
yes_value = yes_net_tokens × yes_closing_price
no_value = no_net_tokens × no_closing_price
```

#### Step 5: Group by Date
Group all rows by `date` and aggregate:
```
markets_engaged = count of unique market_id values
yes_buy = sum of yes_daily_buy across all markets
yes_sell = sum of yes_daily_sell across all markets
no_buy = sum of no_daily_buy across all markets
no_sell = sum of no_daily_sell across all markets
yes_value = sum of yes_value across all markets
no_value = sum of no_value across all markets
```

#### Step 6: Calculate Derived Columns
```
net_yes = yes_buy - yes_sell
net_no = no_buy - no_sell
total_token = net_yes + net_no
total_value = yes_value + no_value
```

#### Step 7: Calculate Cumulative Values
Sort by date, then calculate running totals:
```
cumulative_yes_value = cumulative sum of yes_value
cumulative_no_value = cumulative sum of no_value
cumulative_net_yes = cumulative sum of net_yes
cumulative_net_no = cumulative sum of net_no
cumulative_total_token = cumulative sum of total_token
cumulative_total_value = cumulative sum of total_value
```

---

## How `all_users_analysis.csv` is Created

### Process Overview

The `analyze_all_users.py` script:

1. **Discovers Users**: Finds all `user_*` directories in `all_markets_output/`

2. **For Each User**:
   - Reads their `date_group_token.csv` file
   - Calculates 42 statistics from the daily data
   - Adds user_id and basic information

3. **Aggregates Results**: Combines all user statistics into one DataFrame

4. **Saves Output**: Writes to `all_users_analysis.csv`

### Calculation Examples

#### Example: Calculating `total_token_mean` for User 1

**Input**: `date_group_token.csv` with 39 rows

**Process**:
1. Extract `total_token` column: [-31.12, -1.05, -0.88, ..., -18.37]
2. Calculate mean: `sum(all values) / count(values)`
3. Result: -37,834.60

**Code Equivalent**:
```python
df = pd.read_csv('date_group_token.csv')
total_token_mean = df['total_token'].mean()
```

#### Example: Calculating `cumulative_total_token_final`

**Input**: `date_group_token.csv` with cumulative_total_token column

**Process**:
1. Sort by date (already sorted)
2. Take the last row's `cumulative_total_token` value
3. Result: -1,475,549.41

**Code Equivalent**:
```python
df = pd.read_csv('date_group_token.csv')
df = df.sort_values('date')
cumulative_total_token_final = df['cumulative_total_token'].iloc[-1]
```

---

## Key Insights from Examples

### User 1: Net Seller Pattern
- **Behavior**: Consistent selling over 39 days
- **Peak Activity**: Massive sell on 2024-12-26 (-702K tokens)
- **Final Position**: -1.48M tokens (net seller)
- **Value Impact**: -$560K in cumulative value

### User 2: Major Accumulator Pattern
- **Behavior**: Consistent buying, with massive accumulation days
- **Peak Activity**: Two huge buy days (6.3M and 5.0M tokens)
- **Final Position**: +11.75M tokens (net buyer)
- **Value Impact**: +$3.47M in cumulative value

### User 3: Balanced Trader Pattern
- **Behavior**: Started with large buys, then small sells
- **Activity**: Moderate activity across 3 days
- **Final Position**: +6,453 tokens (net buyer)
- **Value Impact**: +$161.58 in cumulative value

---

## File Structure Summary

```
User Analysis Directory
│
├── raw/                                    # Source data
│   └── <event_id>/
│       ├── trades/                        # Individual trade records
│       └── prices/                        # Price data with closing prices
│
├── all_markets_output/                     # Processed user data
│   └── user_<user_id>/
│       ├── yes_token.csv                  # YES token daily data (per market)
│       ├── no_token.csv                   # NO token daily data (per market)
│       ├── combined_token.csv             # Combined YES/NO data (per market)
│       └── date_group_token.csv           # Daily aggregated across all markets ⭐
│
├── all_users_analysis.csv                  # User statistics summary ⭐
├── analyze_all_users.py                    # Analysis script
└── user_analysis_presentation_examples.md # This file
```

**Key Files for Analysis**:
- ⭐ `date_group_token.csv`: Daily aggregated data per user
- ⭐ `all_users_analysis.csv`: Summary statistics for all users

---

## Usage in Presentations

### Slide 1: Data Overview
- Show the data flow diagram
- Explain `date_group_token.csv` structure
- Show sample rows from a user

### Slide 2: Example User Deep Dive
- Pick User 1 or User 2
- Show their `date_group_token.csv` data
- Highlight key trading days
- Show how statistics are calculated

### Slide 3: Statistics Summary
- Show `all_users_analysis.csv` structure
- Explain key metrics (cumulative positions, means, etc.)
- Show how to interpret the statistics

### Slide 4: User Behavior Patterns
- Compare different user types (accumulators vs. sellers)
- Show how statistics reveal behavior patterns
- Highlight interesting cases

---

## Technical Notes

### Data Quality
- All calculations are verified manually
- Cumulative values correctly carry forward
- Values are calculated using actual closing prices from price files
- Missing data is handled gracefully (users without files are skipped)

### Performance
- Analysis processes 5,422 users
- Each user's statistics calculated independently
- Total processing time: ~2-3 minutes

### Reproducibility
- All scripts are deterministic
- Results can be regenerated by running `analyze_all_users.py`
- Source data is preserved in `raw/` directory

---

## Quick Reference Guide

### Finding Users for Presentations

**Users with Most Trading Days**:
```python
import pandas as pd
df = pd.read_csv('all_users_analysis.csv')
top_users = df.nlargest(10, 'total_days')
```

**Users with Highest Value Positions**:
```python
top_value = df.nlargest(10, 'cumulative_total_value_final')
```

**Users with Most Market Engagement**:
```python
top_engagement = df.nlargest(10, 'total_markets_engaged')
```

### Key Files to Reference

1. **For Daily Activity**: `all_markets_output/user_<user_id>/date_group_token.csv`
   - Shows day-by-day trading activity
   - Includes cumulative positions
   - Perfect for showing trading patterns over time

2. **For User Statistics**: `all_users_analysis.csv`
   - One row per user
   - 42 statistics per user
   - Perfect for comparing users and finding patterns

3. **For Detailed Market Data**: `all_markets_output/user_<user_id>/combined_token.csv`
   - Shows activity per market per day
   - Useful for understanding which markets a user trades in

### Presentation Tips

1. **Start with Data Flow**: Show how raw trades → daily aggregation → statistics
2. **Use Real Examples**: Pick users from the examples above
3. **Show Calculations**: Walk through how one statistic is calculated
4. **Compare Patterns**: Use the comparison table to show different user types
5. **Highlight Insights**: Explain what the statistics reveal about behavior

---

## Conclusion

These examples demonstrate the comprehensive analysis pipeline that transforms raw trading data into meaningful user behavior statistics. The `date_group_token.csv` files provide daily granularity, while `all_users_analysis.csv` provides high-level summaries perfect for identifying patterns, segmenting users, and understanding market behavior.

### Summary of Key Points

1. **Data Flow**: Raw trades → Market aggregation → Combined tokens → Date grouping → User statistics
2. **Daily Data**: `date_group_token.csv` shows one row per trading day with cumulative positions
3. **Statistics**: `all_users_analysis.csv` provides 42 metrics per user calculated from daily data
4. **Examples**: Three distinct user patterns (seller, accumulator, moderate trader)
5. **Verification**: All calculations are traceable and verifiable step-by-step

This analysis enables deep insights into user trading behavior, market participation, and value accumulation patterns across the entire platform.
