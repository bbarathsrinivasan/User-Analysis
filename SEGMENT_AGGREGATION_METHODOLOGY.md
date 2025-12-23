# Segment Aggregation and Odds Comparison Methodology

This document explains how we calculate segment-based aggregated positions, compute investment-based odds, and create comparison graphs that contrast market price-based odds with investment-based odds across user segments.

---

## Table of Contents

1. [Overview](#overview)
2. [Step-by-Step Calculation Process](#step-by-step-calculation-process)
3. [Graph Creation Process](#graph-creation-process)
4. [Example 1: Arizona Senate Election - Close Race with Segment Divergence](#example-1-arizona-senate-election---close-race-with-segment-divergence)
5. [Example 2: New Jersey Senate Election - Strong Republican Position](#example-2-new-jersey-senate-election---strong-republican-position)
6. [Example 3: Market with Early Consensus](#example-3-market-with-early-consensus)
7. [Key Insights and Interpretations](#key-insights-and-interpretations)

---

## Overview

For each prediction market, we create **investment-based odds** by aggregating individual user positions across three segments (Small, Medium, Large) and comparing them with **price-based market odds** from Polymarket. This allows us to:

- Identify when different user segments have different views than the market
- Detect early signals from large investors vs. small investors
- Understand how cumulative investment positions evolve over time
- Compare market sentiment (prices) with actual capital allocation (investments)

---

## Step-by-Step Calculation Process

### Step 1: Load User Segment Mapping

**Source**: `all_users_analysis.csv`

We load the user segment classification (Small, Medium, Large) for each user based on their total trading activity:

```python
segment_map = {
    "0xuser1": "Small",
    "0xuser2": "Medium",
    "0xuser3": "Large",
    ...
}
```

**Segmentation Criteria**: Users are classified based on their total trading volume and activity across all markets, as calculated in `all_users_analysis.csv`.

### Step 2: Load Individual User Positions

**Source**: `segment_output/<event_id>/<market_slug>/user_<user_id>.csv`

For each market, we load all user position files. Each file contains daily data with:

- `day_offset`: Days from market closing (0 = closing day)
- `yes_cumulative_position`: User's cumulative YES token position
- `no_cumulative_position`: User's cumulative NO token position
- `individual_yes_position`: Calculated individual YES exposure (accounts for short positions)
- `individual_no_position`: Calculated individual NO exposure (accounts for short positions)

**Key Point**: We use `individual_yes_position` and `individual_no_position` rather than raw cumulative positions because these account for short selling (negative positions contribute to the opposite side).

### Step 3: Aggregate Positions by Segment

For each `day_offset` and each segment (All, Small, Medium, Large), we calculate:

#### 3.1 Aggregate YES Positions (`agg_yes`)

```
agg_yes = Σ(individual_yes_position) 
         for all users in segment 
         where yes_cumulative_position != 0
```

**Rationale**: We only include users who have an active YES position (non-zero cumulative position). This ensures we're measuring actual YES exposure, not just users with zero positions.

#### 3.2 Aggregate NO Positions (`agg_no`)

```
agg_no = Σ(individual_no_position) 
        for all users in segment 
        where no_cumulative_position != 0
```

**Rationale**: Similarly, we only include users with active NO positions.

#### 3.3 Calculate Investment-Based Odds

```
odds = agg_yes / (agg_yes + agg_no)
```

**Interpretation**: 
- `odds = 0.0` means all investment is on NO
- `odds = 1.0` means all investment is on YES
- `odds = 0.5` means equal investment on both sides

**Edge Cases**:
- If `agg_yes + agg_no == 0`, we set `odds = NaN` (no users with positions that day)
- If only one side has investment, odds will be 0.0 or 1.0

### Step 4: Load Price-Based Market Odds

**Source**: `raw/<event_id>/prices/<market_slug>_closing_prices.csv`

We extract YES closing prices from the price file:

1. Filter rows where `token_type == "YES"`
2. Extract `date` and `closing_price` columns
3. Convert dates to `day_offset` by finding the market's closing date (day_offset = 0)
4. Use YES `closing_price` directly as the price-based odds

**Rationale**: In prediction markets, the YES token price represents the market's implied probability that the event will occur. A YES price of 0.75 means the market believes there's a 75% chance the event happens.

### Step 5: Create Output Files

For each market, we create 4 CSV files in `segment/<event_id>/<market_slug>/`:

1. **`all_segments.csv`**: Aggregated across all users
2. **`small_segment.csv`**: Only Small segment users
3. **`medium_segment.csv`**: Only Medium segment users
4. **`large_segment.csv`**: Only Large segment users

Each CSV has columns:
- `day_offset`: Days from closing (negative = earlier, 0 = closing day)
- `agg_yes`: Sum of individual YES positions
- `agg_no`: Sum of individual NO positions
- `odds`: Investment-based odds (agg_yes / (agg_yes + agg_no))

---

## Graph Creation Process

### Step 1: Prepare Data

We load:
- Price-based odds from price file (already in day_offset format)
- Investment-based odds from the 4 CSV files (all_segments, small, medium, large)

### Step 2: Create 5-Line Comparison Graph

**Graph Specifications**:
- **X-axis**: `day_offset` (days from closing, 0 = closing day)
- **Y-axis**: `odds` (0.0 to 1.0, probability scale)
- **Title**: Market slug (e.g., "Will Gallego win Arizona Senate election by 0-1%?")

**5 Lines**:

1. **Price-based Market Odds** (Blue, solid line with circles)
   - Source: YES closing prices from Polymarket
   - Represents: Market sentiment / consensus probability

2. **All Segments Investment-based Odds** (Green, solid line with squares)
   - Source: `all_segments.csv`
   - Represents: Overall capital allocation across all users

3. **Small Segment Investment-based Odds** (Orange, solid line with triangles)
   - Source: `small_segment.csv`
   - Represents: Small investors' capital allocation

4. **Medium Segment Investment-based Odds** (Red, solid line with inverted triangles)
   - Source: `medium_segment.csv`
   - Represents: Medium investors' capital allocation

5. **Large Segment Investment-based Odds** (Purple, solid line with diamonds)
   - Source: `large_segment.csv`
   - Represents: Large investors' capital allocation

**Visual Features**:
- Grid enabled for readability
- Legend showing all 5 lines
- Y-axis limited to [0, 1] for probability scale
- Different markers for each line to aid distinction
- High-resolution output (300 DPI) for publication quality

### Step 3: Save Graph

Graphs are saved as `odds_comparison.png` in each market's segment folder.

---

## Example 1: Arizona Senate Election - Close Race with Segment Divergence

**Market**: `will-gallego-win-arizona-senate-election-by-0-1`

**Context**: This market asks whether Ruben Gallego will win the Arizona Senate election by 0-1% margin. This is a very close outcome prediction.

### Data Summary

**All Segments** (day_offset = 0):
- `agg_yes = 97,108.64`
- `agg_no = 96,018.74`
- `odds = 0.503` (essentially 50/50)

**Small Segment** (day_offset = 0):
- `agg_yes = 88,150.91`
- `agg_no = 431.93`
- `odds = 0.995` (strong YES position)

**Medium Segment** (day_offset = 0):
- `agg_yes = 5,657.92`
- `agg_no = 10,008.42`
- `odds = 0.361` (moderate NO position)

**Large Segment** (day_offset = 0):
- `agg_yes = 3,299.81`
- `agg_no = 85,578.38`
- `odds = 0.037` (very strong NO position)

### Graph Interpretation

**Key Observations**:

1. **Strong Segment Divergence**: 
   - Small investors are heavily betting YES (odds ≈ 0.995)
   - Large investors are heavily betting NO (odds ≈ 0.037)
   - Medium investors are moderately NO (odds ≈ 0.36)
   - This creates a dramatic split in the graph

2. **Price vs. Investment Divergence**:
   - Market prices show YES odds around 0.001-0.05 (very low)
   - Small segment investment odds are near 1.0 (very high)
   - Large segment investment odds are near 0.0 (very low)
   - All-segments combined shows ~50/50, masking the internal divergence

3. **Temporal Evolution**:
   - Early days (day_offset = -18 to -15): Small segment builds strong YES position
   - Mid-period: Large segment accumulates NO position
   - Closing: Divergence remains strong

### Insights

**What This Tells Us**:

1. **Information Asymmetry**: Large investors (who likely have more information/research) are betting against small investors. This suggests:
   - Large investors may have better information about the actual outcome
   - Small investors may be following sentiment or less-informed analysis

2. **Market Efficiency Question**: The price-based odds (very low YES) align more with large investors than small investors, suggesting:
   - Market prices may be driven by informed large traders
   - Small investors' capital allocation doesn't match market prices

3. **Risk Profile**: Small investors are taking a contrarian position relative to both market prices and large investors, which could indicate:
   - Higher risk tolerance
   - Different information sources
   - Potential mispricing opportunity (if small investors are correct)

4. **Market Structure**: The fact that all-segments combined shows ~50/50 while individual segments show extreme positions suggests:
   - Segments are effectively betting against each other
   - The market is balanced in aggregate but polarized by segment

---

## Example 2: New Jersey Senate Election - Strong Republican Position

**Market**: `will-the-republicans-win-the-new-jersey-senate-race-in-2026`

**Context**: This market asks whether Republicans will win the New Jersey Senate race in 2026. New Jersey is traditionally a Democratic-leaning state.

### Data Summary

**All Segments** (day_offset = 0):
- `agg_yes = 987.33`
- `agg_no = 1,581.10`
- `odds = 0.384` (moderate NO position)

**Small Segment** (day_offset = 0):
- `agg_yes = 450.0`
- `agg_no = 40.0`
- `odds = 0.918` (strong YES position)

**Medium Segment**:
- Data shows moderate activity

**Large Segment**:
- Data shows moderate activity

### Graph Interpretation

**Key Observations**:

1. **Early Strong Position**: 
   - Small segment establishes strong YES position early (odds ≈ 0.92)
   - This position remains stable throughout the trading period

2. **Market Price Evolution**:
   - Price-based odds start around 0.54 (slight YES favor)
   - Prices decline over time to near 0.0 (strong NO favor)
   - This represents a significant shift in market sentiment

3. **Investment vs. Price Divergence**:
   - Small segment maintains high YES investment (0.92) even as prices drop
   - All-segments combined shows moderate NO (0.38)
   - Large segments may be driving the overall NO position

### Insights

**What This Tells Us**:

1. **Sticky Positions**: Small investors established a strong YES position early and maintained it despite:
   - Declining market prices
   - Changing market sentiment
   - This suggests conviction or lack of information updating

2. **Market Sentiment Shift**: The price decline from 0.54 to near 0.0 suggests:
   - New information entered the market
   - Market participants updated their beliefs
   - Small investors did not update their positions accordingly

3. **Contrarian Behavior**: Small investors betting YES in a Democratic-leaning state could indicate:
   - They see value in a contrarian position
   - They have different information or analysis
   - They may be less informed about political fundamentals

4. **Risk-Reward**: If small investors are correct and Republicans do win, they would profit significantly given the low market prices. However, the low prices suggest this is unlikely.

---

## Example 3: Market with Early Consensus

**Market**: Markets where all segments and prices converge early

### Pattern Characteristics

When examining markets with early consensus, we typically see:

1. **Convergence**: All lines (price-based and all segment investment-based) converge to similar values early in the trading period

2. **Stability**: Once converged, the lines remain stable with minimal divergence

3. **Low Volatility**: Small day-to-day changes in odds

### Example Pattern

```
Day_offset: -30  -25  -20  -15  -10  -5   0
Price:       0.65 0.68 0.70 0.72 0.72 0.73 0.73
All Seg:     0.60 0.65 0.68 0.70 0.71 0.72 0.72
Small:       0.58 0.63 0.67 0.69 0.70 0.71 0.71
Medium:      0.62 0.67 0.69 0.71 0.72 0.73 0.73
Large:       0.65 0.70 0.72 0.73 0.73 0.74 0.74
```

### Graph Interpretation

**Key Observations**:

1. **Early Information Processing**: 
   - All segments and prices converge within the first 10-15 days
   - This suggests information was quickly incorporated

2. **Consensus Building**: 
   - Segments start with slightly different views
   - They converge as more information becomes available
   - Final consensus reflects shared understanding

3. **Market Efficiency**: 
   - Price-based odds align closely with investment-based odds
   - This suggests the market is efficiently incorporating information
   - No significant mispricing opportunities

### Insights

**What This Tells Us**:

1. **Information Quality**: When all segments converge, it suggests:
   - High-quality, widely-available information
   - Clear outcome signals
   - Low information asymmetry

2. **Market Maturity**: Early convergence indicates:
   - Well-functioning market
   - Efficient price discovery
   - Informed participants across segments

3. **Predictability**: Stable, converged odds suggest:
   - Outcome is relatively predictable
   - Low uncertainty
   - Consensus view is well-founded

4. **Trading Strategy**: In such markets:
   - Early positions are most valuable
   - Later trading provides minimal edge
   - Arbitrage opportunities are limited

---

## Key Insights and Interpretations

### General Patterns to Look For

#### 1. **Segment Divergence**

**What it means**: Different user segments have different views

**How to identify**: Lines spread apart, especially Small vs. Large

**Interpretation**:
- Information asymmetry between segments
- Different risk preferences
- Different information sources or analysis methods
- Potential mispricing if one segment is correct

#### 2. **Price-Investment Divergence**

**What it means**: Market prices don't align with capital allocation

**How to identify**: Price-based line (blue) diverges from investment-based lines

**Interpretation**:
- Market sentiment vs. actual capital commitment
- Potential arbitrage opportunities
- One measure may be more accurate than the other
- Market manipulation or liquidity issues

#### 3. **Early vs. Late Position Changes**

**What it means**: How positions evolve over time

**How to identify**: Lines shift significantly during the trading period

**Interpretation**:
- **Early shifts**: New information enters market, informed traders act first
- **Late shifts**: Last-minute information, panic buying/selling, or position adjustments
- **Stable lines**: Strong conviction, no new information, or locked positions

#### 4. **Segment-Specific Patterns**

**Small Segment**:
- Often shows higher volatility
- May take contrarian positions
- Could indicate retail sentiment vs. institutional view

**Large Segment**:
- Typically more stable
- May lead price movements
- Could indicate informed money or institutional analysis

**Medium Segment**:
- Often between Small and Large
- May represent moderate investors
- Could indicate balanced risk approach

### Analytical Framework

When analyzing a graph, ask:

1. **Convergence**: Do all lines converge or diverge?
   - Convergence → Consensus, efficient market
   - Divergence → Disagreement, potential mispricing

2. **Direction**: Are segments moving in the same direction?
   - Same direction → Shared information or sentiment
   - Opposite directions → Information asymmetry or different strategies

3. **Timing**: When do major shifts occur?
   - Early → Information quickly incorporated
   - Late → Last-minute information or position adjustments

4. **Magnitude**: How large are the differences?
   - Small differences → Minor disagreement
   - Large differences → Fundamental disagreement or mispricing

5. **Stability**: Do positions remain stable or change frequently?
   - Stable → Strong conviction
   - Volatile → Uncertainty or active trading

### Practical Applications

#### For Researchers

- **Market Efficiency**: Compare price-based vs. investment-based odds to assess market efficiency
- **Information Flow**: Track how information propagates across segments
- **Behavioral Finance**: Understand how different investor types behave

#### For Traders

- **Arbitrage Opportunities**: Identify when prices diverge from investment positions
- **Sentiment Analysis**: Use segment positions to gauge market sentiment
- **Risk Assessment**: Understand which segments are taking which positions

#### For Market Analysts

- **Predictive Power**: Determine if investment-based odds predict outcomes better than prices
- **Market Structure**: Understand how different investor segments contribute to price formation
- **Regulatory Insights**: Identify potential market manipulation or information asymmetry

---

## Technical Notes

### Data Quality Considerations

1. **Missing Users**: Users without segment mappings are excluded from segment-specific calculations but included in "all segments"

2. **Zero Positions**: Days with no users having positions result in `odds = NaN` (not plotted)

3. **Price Data Alignment**: Price data is aligned to day_offset using the market's closing date. If price data is missing for some days, those days won't have price-based odds plotted.

4. **Position Calculation**: Individual positions account for short selling (negative cumulative positions contribute to opposite side), ensuring accurate exposure measurement.

### Limitations

1. **Segment Classification**: Segments are based on overall trading activity, not market-specific activity. A "Large" trader in one market may be inactive in another.

2. **Temporal Alignment**: Price data and investment data may have slight timing differences (end-of-day prices vs. cumulative positions).

3. **Liquidity**: Markets with low liquidity may show more volatile or less reliable patterns.

4. **Selection Bias**: Only users with segment mappings are included, which may not represent all market participants.

---

## Conclusion

The segment aggregation and odds comparison methodology provides a powerful lens for understanding prediction market dynamics. By comparing price-based market odds with investment-based odds across user segments, we can:

- Identify information asymmetry
- Detect potential mispricing
- Understand investor behavior
- Assess market efficiency
- Generate trading insights

The examples provided demonstrate different market patterns and their interpretations, serving as a guide for analyzing similar graphs across all markets in the dataset.

