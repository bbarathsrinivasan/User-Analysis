# All Users Analysis Methodology

## Overview

This document explains how the user behavior analysis was performed using data from `date_group_token.csv` files. The analysis calculates comprehensive statistics for each user to understand their trading patterns, activity levels, and value changes over time.

---

## Data Source

For each user, the analysis is based on their `date_group_token.csv` file, which contains daily aggregated trading data with the following key columns:
- `total_token`: Net tokens traded per day (net_yes + net_no)
- `total_value`: Net value per day (yes_value + no_value)
- `cumulative_total_token`: Running total of tokens
- `cumulative_total_value`: Running total of value
- `net_yes`, `net_no`: Net YES/NO tokens per day
- `yes_value`, `no_value`: YES/NO values per day
- `markets_engaged`: Number of markets the user engaged in per day

---

## Statistics Calculated

The analysis calculates **42 statistics** for each user:

### 1. Basic Information (4 statistics)
- **total_days**: Number of days the user has trading activity
- **first_date**: Date of first trading activity
- **last_date**: Date of last trading activity
- **date_range_days**: Number of days between first and last activity

### 2. Total Token Statistics (5 statistics)
- **total_token_min**: Minimum daily total_token value
- **total_token_max**: Maximum daily total_token value
- **total_token_mean**: Average daily total_token
- **total_token_median**: Median daily total_token
- **total_token_sum**: Sum of all daily total_token values

### 3. Total Value Statistics (5 statistics)
- **total_value_min**: Minimum daily total_value
- **total_value_max**: Maximum daily total_value
- **total_value_mean**: Average daily total_value
- **total_value_median**: Median daily total_value
- **total_value_sum**: Sum of all daily total_value values

### 4. Cumulative Statistics (6 statistics)
- **cumulative_total_token_final**: Final cumulative token position
- **cumulative_total_token_max**: Maximum cumulative token position reached
- **cumulative_total_token_min**: Minimum cumulative token position reached
- **cumulative_total_value_final**: Final cumulative value position
- **cumulative_total_value_max**: Maximum cumulative value position reached
- **cumulative_total_value_min**: Minimum cumulative value position reached

### 5. Net YES/NO Statistics (10 statistics)
- **net_yes_min/max/mean/sum**: Statistics for net YES tokens
- **net_yes_final_cumulative**: Final cumulative net YES position
- **net_no_min/max/mean/sum**: Statistics for net NO tokens
- **net_no_final_cumulative**: Final cumulative net NO position

### 6. YES/NO Value Statistics (10 statistics)
- **yes_value_min/max/mean/sum**: Statistics for YES token values
- **yes_value_final_cumulative**: Final cumulative YES value
- **no_value_min/max/mean/sum**: Statistics for NO token values
- **no_value_final_cumulative**: Final cumulative NO value

### 7. Trading Activity Statistics (1 statistic)
- **total_markets_engaged**: Total number of market engagements across all days

---

## Step-by-Step Example: User 0xa58d4f278d7953cd38eeb929f7e242bfc7c0b9b8

### Raw Data

| Date | total_token | total_value | cumulative_total_token | cumulative_total_value |
|------|-------------|-------------|------------------------|-----------------------|
| 2025-10-14 | 7142.35 | 542.38275 | 7142.35 | 542.38275 |
| 2025-10-19 | -667.38 | -378.4983 | 6474.97 | 163.88445 |
| 2025-11-14 | -21.97 | -2.30685 | 6453.0 | 161.57760 |

### Calculation Steps

#### Step 1: Basic Information
```
total_days = 3 (number of rows)
first_date = 2025-10-14 (earliest date)
last_date = 2025-11-14 (latest date)
date_range_days = (2025-11-14) - (2025-10-14) = 31 days
```

#### Step 2: Total Token Statistics

**Data Array**: [7142.35, -667.38, -21.97]

```
total_token_min = min(7142.35, -667.38, -21.97) = -667.38
total_token_max = max(7142.35, -667.38, -21.97) = 7142.35
total_token_mean = (7142.35 + (-667.38) + (-21.97)) / 3 = 2151.00
total_token_median = median(7142.35, -667.38, -21.97) = -21.97
total_token_sum = 7142.35 + (-667.38) + (-21.97) = 6453.00
```
✅ **Verified**: All values match the CSV output


#### Step 3: Total Value Statistics

**Data Array**: [542.38275, -378.4983, -2.30685]

```
total_value_min = min(542.38275, -378.4983, -2.30685) = -378.49830
total_value_max = max(542.38275, -378.4983, -2.30685) = 542.38275
total_value_mean = (542.38275 + (-378.4983) + (-2.30685)) / 3 = 53.85920
total_value_median = median(542.38275, -378.4983, -2.30685) = -2.30685
total_value_sum = 542.38275 + (-378.4983) + (-2.30685) = 161.57760
```
✅ **Verified**: All values match the CSV output


#### Step 4: Cumulative Statistics

```
cumulative_total_token_final = 6453.0 (last row's cumulative value)
cumulative_total_token_max = max(7142.35, 6474.97, 6453.0) = 7142.35
cumulative_total_token_min = min(7142.35, 6474.97, 6453.0) = 6453.0

cumulative_total_value_final = 161.57760 (last row's cumulative value)
cumulative_total_value_max = max(542.38275, 163.88445, 161.57760) = 542.38275
cumulative_total_value_min = min(542.38275, 163.88445, 161.57760) = 161.57760
```

#### Step 5: Trading Activity Statistics

From the raw data:
- Day 1: markets_engaged = 13
- Day 2: markets_engaged = 4
- Day 3: markets_engaged = 1

```
total_markets_engaged = 13 + 4 + 1 = 18
```

---

## Interpretation of Statistics

### User Behavior Patterns

1. **Accumulators** (high cumulative_total_token_final):
   - Users who have accumulated large net positions
   - May indicate long-term holding strategy

2. **Distributors** (negative cumulative_total_token_final):
   - Users who have net sold positions
   - May indicate profit-taking or exit strategy

3. **Active Traders** (high total_markets_engaged):
   - Users who engage in many markets
   - May indicate diversified trading strategy

4. **High Value Users** (high cumulative_total_value_final):
   - Users with significant value positions
   - May indicate successful trading or large positions

### Key Metrics to Watch

- **cumulative_total_token_final**: Final net position (positive = net buyer, negative = net seller)
- **cumulative_total_value_final**: Final net value position
- **total_markets_engaged**: Total engagement level (higher = more active across markets)
- **total_token_mean**: Average daily activity level
- **total_value_mean**: Average daily value change

---

## Output File

The analysis generates `all_users_analysis.csv` with one row per user containing all 42 calculated statistics. This file can be used for:
- Identifying user segments
- Finding highly active users
- Analyzing trading patterns
- Understanding market behavior
- Risk assessment

---

## Technical Details

### Handling Edge Cases
- **Missing data**: Users without `date_group_token.csv` are skipped
- **Empty files**: Users with empty date_group_token.csv files are skipped
- **Single day users**: All statistics are calculated normally (mean = median = single value)

---

## Verification

All calculations have been verified using the example user `0xa58d4f278d7953cd38eeb929f7e242bfc7c0b9b8` with step-by-step manual calculations matching the automated results.

---

## Usage

To regenerate the analysis:
```bash
python analyze_all_users.py
```

This will create/update `all_users_analysis.csv` with statistics for all users who have `date_group_token.csv` files.
