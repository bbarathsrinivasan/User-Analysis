# Date Group Token Calculation Verification

## User: 0xa58d4f278d7953cd38eeb929f7e242bfc7c0b9b8

This document provides a manual calculation breakdown for the `date_group_token.csv` file to verify the `yes_value` and `no_value` calculations.

**Calculation Method**: For each row, `yes_value = yes_net_tokens × yes_closing_price` and `no_value = no_net_tokens × no_closing_price`, then sum across all markets for each date.

---

## Date: 2025-10-14

### Summary
- **Markets Engaged**: 13 unique markets
- **YES Buy Total**: 2400.0 tokens
- **NO Buy Total**: 4742.35 tokens
- **YES Value**: 172.86
- **NO Value**: 369.52275

---

## YES Value Calculation

For each market, we multiply `yes_net_tokens` by the `yes_closing_price` for that market on that date, then sum all values.

| Market | yes_net_tokens | yes_closing_price | Calculation | yes_value |
|--------|----------------|------------------|-------------|-----------|
| will-the-democrats-win-the-mississippi-senate-race-in-2026 | 128.0 | 0.085 | 128.0 × 0.085 | 10.880 |
| will-the-democrats-win-the-tennessee-senate-race-in-2026 | 50.0 | 0.075 | 50.0 × 0.075 | 3.750 |
| will-the-democrats-win-the-west-virginia-senate-race-in-2026 | 170.0 | 0.075 | 170.0 × 0.075 | 12.750 |
| will-the-democrats-win-the-wyoming-senate-race-in-2026 | 955.0 | 0.075 | 955.0 × 0.075 | 71.625 |
| will-the-republicans-win-the-massachusetts-senate-race-in-2026 | 927.0 | 0.065 | 927.0 × 0.065 | 60.255 |
| will-the-republicans-win-the-rhode-island-senate-race-in-2026 | 170.0 | 0.080 | 170.0 × 0.080 | 13.600 |

**Total YES Value**: 10.880 + 3.750 + 12.750 + 71.625 + 60.255 + 13.600 = **172.860**

**Verification**: ✅ Matches `date_group_token.csv` value of 172.86

---

## NO Value Calculation

For each market, we multiply `no_net_tokens` by the `no_closing_price` for that market on that date, then sum all values.

| Market | no_net_tokens | no_closing_price | Calculation | no_value |
|--------|---------------|------------------|-------------|----------|
| will-the-democrats-win-the-delaware-senate-race-in-2026 | 170.00 | 0.085 | 170.00 × 0.085 | 14.45000 |
| will-the-democrats-win-the-massachusetts-senate-race-in-2026 | 1636.35 | 0.065 | 1636.35 × 0.065 | 106.36275 |
| will-the-democrats-win-the-rhode-island-senate-race-in-2026 | 170.00 | 0.080 | 170.00 × 0.080 | 13.60000 |
| will-the-republicans-win-the-mississippi-senate-race-in-2026 | 141.00 | 0.085 | 141.00 × 0.085 | 11.98500 |
| will-the-republicans-win-the-tennessee-senate-race-in-2026 | 865.00 | 0.085 | 865.00 × 0.085 | 73.52500 |
| will-the-republicans-win-the-west-virginia-senate-race-in-2026 | 855.00 | 0.085 | 855.00 × 0.085 | 72.67500 |
| will-the-republicans-win-the-wyoming-senate-race-in-2026 | 905.00 | 0.085 | 905.00 × 0.085 | 76.92500 |

**Total NO Value**: 14.45000 + 106.36275 + 13.60000 + 11.98500 + 73.52500 + 72.67500 + 76.92500 = **369.52275**

**Verification**: ✅ Matches `date_group_token.csv` value of 369.52275

---

## Date: 2025-10-19

### Summary
- **Markets Engaged**: 4 unique markets
- **YES Buy Total**: 0.0 tokens
- **YES Sell Total**: 0.0 tokens
- **NO Buy Total**: 0.0 tokens
- **NO Sell Total**: 667.38 tokens
- **YES Value**: 0.0
- **NO Value**: -378.4983

### Market Details

| Market | yes_net_tokens | yes_closing_price | no_net_tokens | no_closing_price |
|--------|----------------|-------------------|---------------|------------------|
| will-the-democrats-win-the-maine-senate-race-in-2026 | 0.0 | - | -299.98 | 0.435 |
| will-the-republicans-win-the-new-jersey-senate-race-in-2026 | 0.0 | - | -225.00 | 0.895 |
| will-the-republicans-win-the-ohio-senate-race-in-2026 | 0.0 | - | -120.00 | 0.355 |
| will-the-republicans-win-the-texas-senate-race-in-2026 | 0.0 | - | -22.40 | 0.180 |

**Total NO Sell**: 299.98 + 225.00 + 120.00 + 22.40 = **667.38** ✅

### Value Calculation

**YES Value**: 
- No YES net tokens on this date (all yes_net_tokens = 0.0)
- Sum of (yes_net_tokens × yes_closing_price) = 0.0 × any_price = **0.0** ✅

**NO Value**: 
- All NO net tokens are negative (sells)
- will-the-democrats-win-the-maine-senate-race-in-2026: -299.98 × 0.435 = **-130.4913**
- will-the-republicans-win-the-new-jersey-senate-race-in-2026: -225.00 × 0.895 = **-201.3750**
- will-the-republicans-win-the-ohio-senate-race-in-2026: -120.00 × 0.355 = **-42.6000**
- will-the-republicans-win-the-texas-senate-race-in-2026: -22.40 × 0.180 = **-4.0320**

**Total NO Value**: -130.4913 + (-201.3750) + (-42.6000) + (-4.0320) = **-378.4983** ✅

**Verification**: ✅ Matches `date_group_token.csv` values:
- YES Value: 0.0
- NO Value: -378.4983

**Note**: This date has NO sells (667.38 tokens), resulting in negative net tokens and negative NO value.

---

## Date: 2025-11-14

### Summary
- **Markets Engaged**: 1 unique market
- **YES Buy Total**: 0.0 tokens
- **YES Sell Total**: 0.0 tokens
- **NO Buy Total**: 0.0 tokens
- **NO Sell Total**: 21.97 tokens
- **YES Value**: 0.0
- **NO Value**: -2.30685

### Market Details

| Market | yes_net_tokens | yes_closing_price | no_net_tokens | no_closing_price |
|--------|----------------|-------------------|---------------|------------------|
| will-the-republicans-win-the-florida-senate-race-in-2026 | 0.0 | - | -21.97 | 0.105 |

**Total NO Sell**: **21.97** ✅

### Value Calculation

**YES Value**: 
- No YES net tokens on this date (yes_net_tokens = 0.0)
- Sum of (yes_net_tokens × yes_closing_price) = 0.0 × any_price = **0.0** ✅

**NO Value**: 
- NO net tokens are negative (sell)
- will-the-republicans-win-the-florida-senate-race-in-2026: -21.97 × 0.105 = **-2.30685** ✅

**Total NO Value**: **-2.30685** ✅

**Verification**: ✅ Matches `date_group_token.csv` values:
- YES Value: 0.0
- NO Value: -2.30685

**Note**: This date has NO sell (21.97 tokens), resulting in negative net tokens and negative NO value.

---

## Calculation Method

1. **Load Data**: Read `combined_token.csv` for the user
2. **Load Closing Prices**: For each unique market (event_id, market_slug), load the corresponding `_closing_prices.csv` file from `raw/<event_id>/prices/`
3. **Merge Prices**: Merge closing prices with combined token data by `event_id`, `market_slug`, and `date`
4. **Calculate Values**: 
   - `yes_value = yes_net_tokens × yes_closing_price` for each row
   - `no_value = no_net_tokens × no_closing_price` for each row
5. **Group by Date**: Sum all values for each date across all markets
6. **Output**: Create one row per date with aggregated values

---

## Key Points

- **Values are calculated per market using net_tokens (not daily_buy), then summed per date**
- **Net tokens can be positive (buys > sells) or negative (sells > buys)**
- **Values reflect the net position value: positive for net buys, negative for net sells**
- **Closing prices come from the `_closing_prices.csv` files in the prices folder**
- **Each day's calculation is independent** (no carry-forward from previous days)
- **Prices are matched by event_id, market_slug, and date**

---

## Verification Status

✅ **All calculations verified and match the generated `date_group_token.csv` file**

### Summary of All Dates

| Date | Markets | YES Value | NO Value | Notes |
|------|---------|-----------|----------|-------|
| 2025-10-14 | 13 | 172.86 | 369.52275 | All net tokens positive (buys only) |
| 2025-10-19 | 4 | 0.0 | -378.4983 | NO net tokens negative (sells only) |
| 2025-11-14 | 1 | 0.0 | -2.30685 | NO net tokens negative (sells only) |
