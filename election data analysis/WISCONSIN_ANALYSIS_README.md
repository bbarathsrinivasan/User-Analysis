# Wisconsin US Senate Election Analysis

## Overview

This analysis examines the **Wisconsin US Senate Election** by comparing prediction market trading behavior with election donation patterns for the two main candidates:
- **Tammy Baldwin (Democrat)** - Incumbent Senator
- **Eric Hovde (Republican)** - Challenger

The analysis combines three data sources:
1. **Market Trading Data** - User trading behavior on prediction markets
2. **Price-Based Market Odds** - Actual market prices reflecting collective market sentiment
3. **Election Donation Data** - Campaign contribution patterns over time

---

## Key Statistics

### Election Donations

**Tammy Baldwin (Democrat)**:
- **Total donations**: $28,123,819.00
- **Donation period**: 910 days (2022-08-05 to 2025-06-30)
- **Number of records**: 211,547 individual donations
- **Average daily donation**: $30,905.30

**Eric Hovde (Republican)**:
- **Total donations**: $12,568,696.00
- **Donation period**: 315 days (2023-08-18 to 2025-06-30)
- **Number of records**: 42,874 individual donations (combining "HOVDE, ERIC" and "HOVDE, ERIC D")
- **Average daily donation**: $39,900.62

### Market Trading Activity

**Democrat Market** (`will-a-democrat-win-wisconsin-us-senate-election`):
- **Total trades**: 659 trades
- **Unique users**: 248 users
- **Trading period**: 217 days (day_offset -216 to 0)

**Republican Market** (`will-a-republican-win-wisconsin-us-senate-election`):
- **Total trades**: 708 trades
- **Unique users**: 291 users
- **Trading period**: 219 days (day_offset -218 to 0)

**Other Party Market** (`will-a-candidate-from-another-party-win-wisconsin-us-senate-election`):
- **Total trades**: 1,348,000 trades
- **Unique users**: 652 users
- **Trading period**: 68 days (day_offset -67 to 0)

---

## Chart Explanations

### 1. Odds Comparison (Original) Charts

**Files:**
- `will-a-democrat-win-wisconsin-us-senate-election/odds_comparison_original.png`
- `will-a-republican-win-wisconsin-us-senate-election/odds_comparison_original.png`

**What They Show:**
These charts compare five different methods of calculating the probability (odds) that a candidate will win, plotted over time relative to the election closing day (Day Offset = 0).

**The Five Lines:**

1. **Price-based Market Odds (Blue line with circles)**
   - **Calculation**: Uses the actual closing price of YES tokens from the prediction market
   - **Method**: Directly reflects what traders are willing to pay for a "YES" outcome
   - **Interpretation**: Represents the market's collective price-based probability assessment
   - **Key Feature**: This is the most direct market signal, showing what the market "thinks" based on actual trading prices

2. **All Segments (Investment-based) (Green line with squares)**
   - **Calculation**: Aggregates all user positions across all segments (Small, Medium, Large)
   - **Formula**: `odds = agg_yes / (agg_yes + agg_no)`
     - `agg_yes` = Sum of all users' `individual_yes_position` values
     - `agg_no` = Sum of all users' `individual_no_position` values
   - **Interpretation**: Shows the probability based on the total investment-weighted positions of all traders
   - **Key Feature**: Represents the collective "bet" of all market participants based on their actual positions

3. **Small Segment (Investment-based) (Orange line with triangles)**
   - **Calculation**: Same formula as "All Segments" but only for users in the Small segment
   - **User Classification**: Users with smaller trading volumes/activity
   - **Interpretation**: Shows how smaller traders are positioning themselves
   - **Key Feature**: Often represents retail/individual trader sentiment

4. **Medium Segment (Investment-based) (Red line with squares)**
   - **Calculation**: Same formula but only for Medium segment users
   - **User Classification**: Users with moderate trading volumes
   - **Interpretation**: Shows positioning of medium-sized traders
   - **Key Feature**: Represents mid-tier market participants

5. **Large Segment (Investment-based) (Purple line with diamonds)**
   - **Calculation**: Same formula but only for Large segment users
   - **User Classification**: Users with large trading volumes/activity
   - **Interpretation**: Shows how large/institutional traders are positioning
   - **Key Feature**: Often represents sophisticated or high-volume traders

**How Individual Positions Are Calculated:**

For each user on each day:
- `H_y` = Cumulative YES position (sum of all YES token purchases minus sales)
- `H_n` = Cumulative NO position (sum of all NO token purchases minus sales)

Then:
- `individual_yes_position` = `H_y` (if H_y > 0) + `-H_n` (if H_n < 0)
- `individual_no_position` = `H_n` (if H_n > 0) + `-H_y` (if H_y < 0)

This captures both direct YES positions and indirect YES positions (via short NO positions).

**Key Observations from the Charts:**

**Democrat Market:**
- Price-based odds consistently show higher probability (0.6-1.0) compared to investment-based odds
- Investment-based odds from all segments hover around 0.3-0.6 for most of the period
- Small and Medium segments show significant volatility
- Large segment shows minimal activity until very close to election day
- Price-based odds spike to 1.0 (100%) at closing day

**Republican Market:**
- Price-based odds start around 0.3, decline to ~0.2, then spike to ~0.35 before dropping to near 0
- Investment-based odds (All/Small segments) show strong activity starting around -75 days, peaking at ~0.65
- Large segment shows dramatic peak around -50 days (reaching ~0.85) before declining
- Medium segment shows minimal activity until very close to election
- All investment-based segments end around 0.4, while price-based ends near 0

---

### 2. Election Donations Charts

**Files:**
- `will-a-democrat-win-wisconsin-us-senate-election/odds_comparison_donations.png`
- `will-a-republican-win-wisconsin-us-senate-election/odds_comparison_donations.png`

**What They Show:**
These charts display the normalized daily election donations over time, showing when campaign contributions were received relative to the election closing day.

**Calculation Method:**

1. **Load Donation Data**
   - Read from `Filtered_US_Election_Donation.csv`
   - Filter for candidate names:
     - Democrat: "BALDWIN, TAMMY"
     - Republican: "HOVDE, ERIC" and "HOVDE, ERIC D" (combined as same candidate)

2. **Parse Dates**
   - Convert "Received" column from MMDDYYYY format to datetime
   - Handle both 7-digit (MDDYYYY) and 8-digit (MMDDYYYY) formats
   - Filter out invalid dates

3. **Calculate Daily Donations**
   - Group by date and sum `Donation_Amount_USD` for each day
   - Calculate total donations across all dates

4. **Normalize Donations**
   - **Formula**: `normalized_donation = daily_donation / total_donation`
   - This gives the proportion of total donations received on each day
   - Example: If total donations = $10M and a day has $100K, normalized = 0.01 (1%)

5. **Map to Day Offset**
   - Market closing date: 2024-11-12 (day_offset = 0)
   - Calculate: `day_offset = (donation_date - closing_date).days`
   - This allows alignment with market trading data

**Key Observations from the Charts:**

**Baldwin (Democrat) Donations:**
- **Early Period** (-850 to -650 days): Very low donation activity, close to 0
- **Mid-Period** (-650 to -200 days): Gradual increase in donation frequency and magnitude
- **Pre-Closing Surge** (-200 to 0 days): Dramatic increase in donation activity
  - Highest peak occurs just before closing day, reaching ~0.012 (1.2% of total donations in a single day)
  - Frequent spikes with increasing magnitude as election approaches
- **Post-Closing** (0 to +250 days): Sharp decline to near-zero levels
  - Some negative values (refunds/adjustments) shortly after day 0
  - Overall activity drops dramatically

**Hovde (Republican) Donations:**
- **Early Period** (< -300 days): Very low activity, mostly at 0
- **Pre-Closing Surge** (-280 to 0 days): Dramatic increase starting around -280 days
  - Frequent sharp spikes with increasing magnitude
  - Highest peak just before closing day, reaching ~0.024 (2.4% of total donations in a single day)
  - Intense activity in final 100 days with spikes exceeding 0.015
- **Post-Closing** (> 0 days): Immediate sharp decline
  - Very low activity (mostly 0) with occasional minor spikes
  - Some negative values indicating refunds/adjustments

**Key Insights:**
- Both candidates show strong donation surges in the months leading up to the election
- Hovde's donations are more concentrated in the pre-election period (315 days vs Baldwin's 910 days)
- Both show highest donation peaks very close to the closing day
- Post-election donation activity drops to near-zero for both candidates

---

## Methodology

### Data Processing Pipeline

The analysis follows a three-step pipeline:

1. **`build_segment_positions.py`**
   - Processes raw trade data
   - Creates per-user, per-market position files
   - Calculates cumulative positions and individual positions
   - Output: `output/segment_positions/wisconsin-us-senate-election-winner/`

2. **`process_donations.py`**
   - Processes election donation data from CSV
   - Combines "HOVDE, ERIC" and "HOVDE, ERIC D" as the same candidate
   - Calculates normalized daily donations
   - Maps donations to day_offset for comparison with market data
   - Output: `output/donations/baldwin_donations.csv` and `hovde_donations.csv`

3. **`build_segment_aggregation.py`**
   - Aggregates user positions by segment (Small, Medium, Large, All)
   - Calculates investment-based odds for each segment
   - Loads price-based odds from market price data
   - Loads donation data and normalizes it
   - Generates comparison graphs
   - Output: `output/segment_aggregation/wisconsin-us-senate-election-winner/`

### Day Offset Calculation

All timelines are normalized to "Day Offset" where:
- **Day Offset = 0**: Election closing day (2024-11-12)
- **Negative values**: Days before closing (e.g., -100 = 100 days before election)
- **Positive values**: Days after closing (e.g., +50 = 50 days after election)

This normalization allows direct comparison between:
- Market trading activity
- Price movements
- Donation patterns

### User Segmentation

Users are classified into segments based on their overall trading activity:
- **Small Segment**: Lower trading volume users
- **Medium Segment**: Moderate trading volume users
- **Large Segment**: High trading volume users

Segmentation is determined by the `all_users_analysis.csv` file which contains user segment mappings.

---

## Combined Analysis (Combined Charts)

The pipeline also generates combined charts (`odds_comparison.png`) that show:
- All 5 odds comparison lines (Price-based + 4 Investment-based segments)
- Plus the normalized donation line

This allows for direct visual comparison of:
- How market odds evolve over time
- How different trader segments position themselves
- How donation patterns correlate with market activity

---

## Output Files

### Segment Aggregation Files
Located in: `output/segment_aggregation/wisconsin-us-senate-election-winner/<market_slug>/`

- `all_segments.csv` - Aggregated odds for all users
- `small_segment.csv` - Aggregated odds for Small segment
- `medium_segment.csv` - Aggregated odds for Medium segment
- `large_segment.csv` - Aggregated odds for Large segment

Each CSV contains:
- `day_offset` - Days from closing (0 = closing day)
- `agg_yes` - Aggregated YES position
- `agg_no` - Aggregated NO position
- `odds` - Calculated odds (agg_yes / (agg_yes + agg_no))

### Charts
- `odds_comparison_original.png` - 5-line odds comparison (no donations)
- `odds_comparison_donations.png` - Donation timeline only
- `odds_comparison.png` - Combined chart with all 6 lines

### Donation Files
Located in: `output/donations/`

- `baldwin_donations.csv` - Processed Baldwin donation data
- `hovde_donations.csv` - Processed Hovde donation data (combined variations)

Each CSV contains:
- `day_offset` - Days from closing
- `date` - Calendar date
- `daily_donation` - Total USD donated on that day
- `normalized_donation` - Daily donation / Total donations (proportion)

---

## Key Findings

1. **Donation Patterns**: Both candidates show strong pre-election donation surges, with Hovde's donations being more concentrated in the final months.

2. **Market Sentiment Divergence**: 
   - For Democrats: Price-based odds are consistently higher than investment-based odds
   - For Republicans: Investment-based odds show higher probability than price-based odds in the final months

3. **Segment Behavior**:
   - Large segment traders show different timing patterns (later entry for Democrats, earlier peak for Republicans)
   - Small and Medium segments often track closely with "All Segments"
   - Medium segment shows minimal activity until very close to election

4. **Temporal Patterns**: All metrics show increased activity and volatility as the election approaches, with dramatic changes in the final days.

---

## Technical Notes

- Market closing date: **2024-11-12** (Day Offset = 0)
- All timestamps converted to UTC for consistency
- Donation data includes both positive and negative values (refunds/adjustments)
- Investment-based odds use forward-fill for missing days to ensure continuous plotting
- Price-based odds use daily closing prices from market data

---

## Files Referenced

- **Donation Source**: `Filtered_US_Election_Donation.csv`
- **User Segments**: `../all_users_analysis.csv`
- **Market Data**: `data/wisconsin-us-senate-election-winner/`
- **Output Directory**: `output/segment_aggregation/wisconsin-us-senate-election-winner/`

---

*Analysis generated on: 2026-01-15*
*Event: wisconsin-us-senate-election-winner*
*Candidates: Tammy Baldwin (D) vs. Eric Hovde (R)*
