## Overview

This document verifies that `build_segment_positions.py` correctly computes **per-market, per-user, per-day** position and value time series, matching the requested specification.

The script:

- **Input**: raw trades under `raw/<event_id>/trades/<market_slug>_trades.csv` and (optionally) daily closing prices under `raw/<event_id>/prices/<market_slug>_closing_prices.csv`.
- **Output**: for each event, each market, and each user with trades in that market, a CSV:
  - `segment_output/<event_id>/<market_slug>/user_<user_id>.csv`

Each per-user CSV has columns:

- `day_offset,timestamp,date,yes_daily_buy,yes_daily_sell,yes_net_tokens,yes_cumulative_position,yes_token_price,yes_cumulative_value,no_daily_buy,no_daily_sell,no_net_tokens,no_cumulative_position,no_token_price,no_cumulative_value,H_y,H_n,individual_yes_position,individual_no_position`

and the following definitions:

- **H_y** = cumulative YES position (per market)
- **H_n** = cumulative NO position (per market)
- **individual_yes_position** = \((H_y \text{ if } H_y > 0) + (-H_n \text{ if } H_n < 0)\)
- **individual_no_position** = \((H_n \text{ if } H_n > 0) + (-H_y \text{ if } H_y < 0)\)

---

## 1. Data flow and transformations

### 1.1 Loading and normalizing trades

For each `event_id` and `market_slug`, the script:

- Reads `raw/<event_id>/trades/<market_slug>_trades.csv`.
- Normalizes to:
  - `user_id` = `proxyWallet`
  - `side` = uppercased `side` (`BUY` / `SELL`)
  - `quantity` = numeric `size`
  - `unix_timestamp` = numeric `timestamp` (seconds since epoch)
  - `event_id` = `eventSlug`
  - `market_slug` = `slug`
  - `token_type` = uppercased `outcome` (`YES` / `NO`)
- Drops rows with invalid `quantity` or `unix_timestamp`.
- Adds:
  - `datetime` = UTC datetime from `unix_timestamp`
  - `date` = calendar date of `datetime`

### 1.2 Computing `day_offset`

Within each market (single `event_id` + `market_slug`), the script:

- Finds `max_date` = latest trading `date` in that market.
- Computes:

  \[
  \text{day\_offset} = \text{date} - \text{max\_date} \quad\text{(in days)}
  \]

So:

- The **last trading day** in a market has `day_offset = 0`.
- Earlier days are negative: \(-1, -2, \dots\)

### 1.3 Aggregating to daily per-user, per-token series

For each market, from the normalized trades:

- Group by `(user_id, token_type, day_offset)` to compute:
  - `daily_buy` = sum of `quantity` where `side == "BUY"`
  - `daily_sell` = sum of `quantity` where `side == "SELL"`
  - `net_tokens` = `daily_buy - daily_sell`
- For each `(user_id, token_type, day_offset)` bucket:
  - `timestamp` = **max** `unix_timestamp` that day (end-of-day proxy)
  - `date` = the calendar `date` (the same within the bucket)

Result: a daily series with columns:

- `user_id, token_type, day_offset, timestamp, date, daily_buy, daily_sell, net_tokens`

### 1.4 Building per-user, per-market DataFrame

For a given user and market, the script:

- Filters all daily rows for that user in that market.
- Splits into:
  - `YES` rows and `NO` rows.
- Collects all `day_offset` values where the user has any YES or NO activity.
- For each such `day_offset`:
  - Chooses `timestamp` and `date` from YES if present, otherwise from NO.
  - Reads or defaults the daily quantities:
    - `yes_daily_buy`, `yes_daily_sell`, `yes_net_tokens`
    - `no_daily_buy`, `no_daily_sell`, `no_net_tokens`

The result is an ordered daily series (sorted by `day_offset`) with per-day YES and NO flows.

### 1.5 Cumulative positions (`H_y`, `H_n`)

From the per-day flows:

- YES cumulative position:

  \[
  \text{yes\_cumulative\_position}[t] = \sum_{\tau \le t} \text{yes\_net\_tokens}[\tau]
  \]

- NO cumulative position:

  \[
  \text{no\_cumulative\_position}[t] = \sum_{\tau \le t} \text{no\_net\_tokens}[\tau]
  \]

Then the script sets:

- `H_y = yes_cumulative_position`
- `H_n = no_cumulative_position`

exactly matching:

- **H_y** = cumulative YES position (per market)
- **H_n** = cumulative NO position (per market)

### 1.6 Daily prices and cumulative values

If `raw/<event_id>/prices/<market_slug>_closing_prices.csv` exists with columns at least:

- `date, token_type, price`

then:

- It is pivoted into:
  - `date, YES, NO` → renamed to `yes_token_price`, `no_token_price`.
- Prices are sorted by date and **forward-filled** so missing later dates use the last known price.
- Merged onto the per-user daily series by `date`.
- Within the user series, token prices are **forward-filled again** to cover days where the user trades but the prices dataset does not have a row for that exact calendar date.

Daily cumulative values are then:

- YES:

  \[
  \text{yes\_cumulative\_value}[t]
  = \text{yes\_cumulative\_position}[t] \times \text{yes\_token\_price}[t]
  \]

- NO:

  \[
  \text{no\_cumulative\_value}[t]
  = \text{no\_cumulative\_position}[t] \times \text{no\_token\_price}[t]
  \]

If prices are missing altogether, token price columns are `NA` and cumulative values are set to 0.0 (since NA is filled with 0.0 in the multiplication step).

### 1.7 Individual YES and NO positions

For each day:

- Let `H_y = yes_cumulative_position` and `H_n = no_cumulative_position`.
- The script defines:

  - **Individual YES position**:

    \[
    \text{individual\_yes\_position}
    = \begin{cases}
      H_y & \text{if } H_y > 0 \\
      0 & \text{otherwise}
    \end{cases}
    + \begin{cases}
      -H_n & \text{if } H_n < 0 \\
      0 & \text{otherwise}
    \end{cases}
    \]

    This matches:

    \[
    (H_y \text{ if } H_y > 0) + (-H_n \text{ if } H_n < 0)
    \]

  - **Individual NO position**:

    \[
    \text{individual\_no\_position}
    = \begin{cases}
      H_n & \text{if } H_n > 0 \\
      0 & \text{otherwise}
    \end{cases}
    + \begin{cases}
      -H_y & \text{if } H_y < 0 \\
      0 & \text{otherwise}
    \end{cases}
    \]

    This matches:

    \[
    (H_n \text{ if } H_n > 0) + (-H_y \text{ if } H_y < 0)
    \]

Thus, the implementation exactly follows the requested formulas.

---

## 2. Worked example (synthetic)

To verify correctness, consider a **single market** and **single user** with the following trades and prices.

### 2.1 Assumptions

- Market has trades on two days: `2024-11-10` and `2024-11-11`.
- Latest trading date is `2024-11-11`, so:
  - `day_offset = -1` for `2024-11-10`
  - `day_offset = 0` for `2024-11-11`

**Trades (raw):**

- `2024-11-10`:
  - YES: BUY 10
  - NO: no trades
- `2024-11-11`:
  - YES: SELL 3
  - NO: BUY 5

**Daily closing prices:**

- `2024-11-10`: YES price = 0.60, NO price = 0.40
- `2024-11-11`: YES price = 0.65, NO price = 0.35

### 2.2 Daily aggregation

On `2024-11-10` (`day_offset = -1`):

- YES:
  - `yes_daily_buy = 10`
  - `yes_daily_sell = 0`
  - `yes_net_tokens = 10 - 0 = 10`
- NO:
  - `no_daily_buy = 0`
  - `no_daily_sell = 0`
  - `no_net_tokens = 0 - 0 = 0`

On `2024-11-11` (`day_offset = 0`):

- YES:
  - `yes_daily_buy = 0`
  - `yes_daily_sell = 3`
  - `yes_net_tokens = 0 - 3 = -3`
- NO:
  - `no_daily_buy = 5`
  - `no_daily_sell = 0`
  - `no_net_tokens = 5 - 0 = 5`

### 2.3 Cumulative positions and H_y / H_n

**YES cumulative position:**

- `day_offset = -1`:

  \[
  \text{yes\_cumulative\_position} = 10
  \]

- `day_offset = 0`:

  \[
  \text{yes\_cumulative\_position} = 10 + (-3) = 7
  \]

**NO cumulative position:**

- `day_offset = -1`:

  \[
  \text{no\_cumulative\_position} = 0
  \]

- `day_offset = 0`:

  \[
  \text{no\_cumulative\_position} = 0 + 5 = 5
  \]

By definition:

- `H_y = yes_cumulative_position`
- `H_n = no_cumulative_position`

So:

- `day_offset = -1`: \(H_y = 10,\; H_n = 0\)
- `day_offset = 0`: \(H_y = 7,\; H_n = 5\)

### 2.4 Individual YES/NO positions

#### Day_offset = -1

- \(H_y = 10 > 0\), \(H_n = 0\)

Individual YES:

- \((H_y \text{ if } H_y > 0) = 10\)
- \((-H_n \text{ if } H_n < 0) = 0\)
- `individual_yes_position = 10 + 0 = 10`

Individual NO:

- \((H_n \text{ if } H_n > 0) = 0\)
- \((-H_y \text{ if } H_y < 0) = 0\)
- `individual_no_position = 0 + 0 = 0`

#### Day_offset = 0

- \(H_y = 7 > 0\), \(H_n = 5 > 0\)

Individual YES:

- \((H_y \text{ if } H_y > 0) = 7\)
- \((-H_n \text{ if } H_n < 0) = 0\)
- `individual_yes_position = 7 + 0 = 7`

Individual NO:

- \((H_n \text{ if } H_n > 0) = 5\)
- \((-H_y \text{ if } H_y < 0) = 0\)
- `individual_no_position = 5 + 0 = 5`

These values are exactly what the script computes via the implemented formulas.

### 2.5 Cumulative values

Using the prices:

- `2024-11-10`: YES = 0.60, NO = 0.40
- `2024-11-11`: YES = 0.65, NO = 0.35

YES cumulative value:

- `day_offset = -1`:

  \[
  \text{yes\_cumulative\_value} = 10 \times 0.60 = 6.0
  \]

- `day_offset = 0`:

  \[
  \text{yes\_cumulative\_value} = 7 \times 0.65 = 4.55
  \]

NO cumulative value:

- `day_offset = -1`:

  \[
  \text{no\_cumulative\_value} = 0 \times 0.40 = 0.0
  \]

- `day_offset = 0`:

  \[
  \text{no\_cumulative\_value} = 5 \times 0.35 = 1.75
  \]

These match exactly the formula:

- `cumulative_position * daily_token_price (with forward-filled prices)`.

---

## 3. Sanity check against an actual output row

In the repository, for example:

- `segment_output/arizona-senate-election-margin-of-victory/will-gallego-win-arizona-senate-election-by-0-1/user_<some_user>.csv`

we see rows of the form:

- `day_offset = -15, -14, ..., 0`
- NO-side trades accumulating from 500 to 1500 tokens.
- `H_y = yes_cumulative_position = 0` on all those days (no YES trades).
- `H_n = no_cumulative_position` matches the running total NO tokens.
- `individual_yes_position = 0` (since \(H_y = 0\) and \(H_n > 0\)).
- `individual_no_position = H_n` (since \(H_n > 0\) and \(H_y = 0\)).

This behavior is consistent with the formulas and the synthetic example above.

---

## 4. Conclusion

- The folder structure and outputs match the requested specification:
  - `segment_output/<event_id>/<market_slug>/user_<user_id>.csv`.
- Per-day flows (`*_daily_buy`, `*_daily_sell`, `*_net_tokens`) are correctly aggregated from trades.
- Cumulative positions (`yes_cumulative_position`, `no_cumulative_position`) correspond exactly to **H_y** and **H_n**.
- `individual_yes_position` and `individual_no_position` are implemented exactly as:
  - \((H_y \text{ if } H_y > 0) + (-H_n \text{ if } H_n < 0)\)
  - \((H_n \text{ if } H_n > 0) + (-H_y \text{ if } H_y < 0)\)
- Cumulative values use cumulative positions times daily token prices (forward-filled as needed).

Therefore, `build_segment_positions.py` implements the requested calculations correctly and produces per-market, per-user CSVs suitable for downstream segment analysis.


