# Per-Market Segment-Wise Daily Net Flow Analysis

## Overview

This analysis generates individual segment-wise daily net flow plots for each market, showing how Small, Medium, and Large user segments trade (buy/sell) on a day-by-day basis within each specific market. Unlike the aggregate cumulative plot, these per-market plots show **daily net flow** (not cumulative), allowing us to see the day-to-day trading patterns of each segment within each market's timeline.

## Methodology

### 1. Data Loading and Preprocessing

**Input Data:**
- **Trades Data**: All trades CSV files from `raw/{event_slug}/trades/{market_slug}_trades.csv`
  - Columns: `proxyWallet` (user_id), `side` (BUY/SELL), `size` (shares), `price`, `timestamp`, `slug` (market_id)
- **User Segments**: `segmentation_results/user_segments.csv`
  - Columns: `user_id`, `segment` (Small/Medium/Large)

**Preprocessing Steps:**
1. Convert `timestamp` to pandas datetime
2. Extract `trade_date = timestamp.floor("D")` for daily granularity
3. Merge trades with user segments on `user_id`
4. Filter out trades for users without segment labels

### 2. Net Flow Calculation

For each trade:
- **BUY trades**: `net_flow = + (shares × price)`
- **SELL trades**: `net_flow = - (shares × price)`

This gives us the net flow direction and magnitude for each individual trade.

### 3. Daily Aggregation by Market and Segment

For each market independently:
1. Filter trades for that specific market
2. Group by `["trade_date", "segment"]`
3. Compute:
   - `daily_net = sum(net_flow)` - Net flow for the day
   - `daily_buy = sum(shares × price)` for BUY trades
   - `daily_sell = sum(shares × price)` for SELL trades
   - `trade_count = count()` of trades

**Important**: Each market is analyzed independently with its own timeline. No cumulative calculation is performed - the y-axis represents daily net movement.

### 4. Plot Generation

For each market:
- **X-axis**: `trade_date` (market-specific timeline)
- **Y-axis**: `daily_net` (daily net flow, not cumulative)
- **Lines**: One line per segment (Small, Medium, Large)
- **Title**: `"Segment-Wise Daily Net Flow — Market {market_id}"`
- **Features**: Legend, grid, zero line reference
- **Log Scale**: Automatically applied when all daily net flow values are positive (helps visualize user-level differences when Large segment dominates)

**Log Scale Logic:**
- Log scale is automatically applied when all daily net flow values across all segments are positive (> 0)
- This helps visualize patterns when Large segment activity is orders of magnitude larger than Small/Medium segments
- When negative values exist, linear scale is used with a zero reference line
- Log scale makes it easier to see patterns in all segments simultaneously when there are large scale differences

### 5. Output Structure

```
user_plots/
  segment_net_flow/
    {market_id}.png          # Plot for each market
  segment_daily_net_flow/
    {market_id}.csv          # Daily aggregated data for each market
```

Each CSV contains columns: `date`, `segment`, `daily_net`, `daily_buy`, `daily_sell`, `trade_count`

## Example Markets and Insights

### Example 1: High-Activity Market with All Segments
**Market**: `will-fischer-win-nebraska-senate-election-by-7-points`  
**Trading Period**: October 30 - December 2, 2024 (34 days)  
**Total Trades**: 1,044 trades across all segments

![Fischer Nebraska Market](user_plots/segment_net_flow/will-fischer-win-nebraska-senate-election-by-7-points.png)

**Key Observations:**
- All three segments (Small, Medium, Large) actively traded
- Small segment: Consistent small positive net flow ($1,904.58 total)
- Medium segment: Mixed activity with some large positive days ($863.00 total)
- Large segment: Sporadic but significant trades ($248.95 total)

**Pattern Analysis:**
- Early days (Oct 30-Nov 5): Medium segment shows strong buying activity
- Mid-period (Nov 6-15): Large segment enters with significant trades
- Late period (Nov 16-Dec 2): All segments show reduced but consistent activity

**Insight**: This market shows balanced participation across all segments, with Medium users being most active throughout the trading period. The plot reveals how different segments enter and exit the market at different times, with Medium segment providing consistent liquidity.

### Example 2: Arizona Senate Election - Active Trading
**Market**: `will-gallego-win-arizona-senate-election-by-1-2`  
**Trading Period**: November 8-26, 2024 (19 days)  
**Total Trades**: 1,465 trades

![Arizona Senate Market](user_plots/segment_net_flow/will-gallego-win-arizona-senate-election-by-1-2.png)

**Key Observations:**
- Large segment dominates with significant daily net flows
- Peak activity on Nov 11-12 with Large segment showing $20K+ daily net flow
- Medium segment shows consistent moderate activity
- Small segment has steady but smaller daily flows

**Pattern Analysis:**
- **Nov 8-10**: Gradual buildup with all segments participating
- **Nov 11-12**: Peak activity - Large segment shows massive buying ($27K+ on Nov 12)
- **Nov 13**: Large segment switches to selling (negative $10K net flow)
- **Nov 14-26**: Declining activity with occasional spikes

**Insight**: Large traders drive major price movements, with a clear pattern of accumulation followed by profit-taking. The Nov 13 sell-off by Large segment suggests position adjustment or profit-taking behavior. The plot clearly shows the dominance of Large segment activity and how it influences market dynamics.

### Example 3: High-Volume Market - Senate Majority Leader
**Market**: `will-john-thune-be-the-next-seante-majority-leader`  
**Trading Period**: December 21, 2024 - January 3, 2025 (14 days)  
**Total Trades**: 887,000+ trades

![John Thune Market](user_plots/segment_net_flow/will-john-thune-be-the-next-seante-majority-leader.png)

**Key Observations:**
- Extremely high-volume market with massive daily flows
- Large segment shows dramatic swings: -$13.5M on Dec 21, +$11.6M on Dec 24
- Medium segment consistently positive with $300K-$1.6M daily flows
- Small segment minimal participation

**Pattern Analysis:**
- **Dec 21**: Large segment massive selling (-$13.5M), Medium buying ($405K)
- **Dec 22-24**: Large segment recovery with significant buying
- **Dec 25-26**: Large segment selling again, Medium segment strong buying
- **Jan 2-3**: Activity tapers but Medium segment remains active

**Insight**: This market shows extreme volatility driven by Large segment traders. The dramatic swings suggest sophisticated trading strategies or position adjustments. Medium segment provides consistent liquidity throughout. The plot reveals the massive scale differences between segments - Large segment activity dwarfs others, making this an excellent example of why log scale helps visualize user-level patterns when available.

### Example 4: Balanced Multi-Segment Market
**Market**: `will-a-republican-win-nebraska-special-senate-election`  
**Trading Period**: 34 days  
**Total Trades**: 130 trades

![Nebraska Special Election Market](user_plots/segment_net_flow/will-a-republican-win-nebraska-special-senate-election.png)

**Key Observations:**
- All three segments participate
- Medium segment: Strong net buyer ($5,881.26 total)
- Small segment: Moderate net buyer ($34.93 total)
- Large segment: Small net buyer ($74.56 total)

**Pattern Analysis:**
- More balanced participation across segments
- Medium segment shows consistent buying behavior
- Lower overall volume but steady activity

**Insight**: This market shows more democratic participation with Medium segment users being the primary drivers, suggesting broader market interest rather than whale-driven activity. The plot shows how all segments contribute more evenly compared to high-volume markets.

### Example 5: High-Volume Market with Extreme Swings
**Market**: `will-john-cornyn-be-the-next-seante-majority-leader`  
**Trading Period**: 23 days  
**Total Trades**: 1,000,000+ trades

![John Cornyn Market](user_plots/segment_net_flow/will-john-cornyn-be-the-next-seante-majority-leader.png)

**Key Observations:**
- Extremely high-volume market with massive scale differences
- Large segment shows extreme daily flows (millions of dollars)
- Medium segment provides consistent moderate activity
- Small segment minimal but present

**Pattern Analysis:**
- Large segment dominates with orders of magnitude larger flows
- Shows clear accumulation and distribution patterns
- Medium segment provides steady liquidity throughout

**Insight**: This market demonstrates why log scale visualization is valuable - when Large segment activity is orders of magnitude larger, log scale helps visualize all segments' patterns simultaneously. The plot reveals the underlying structure of market participation across segments.

### Example 6: Log Scale Market - All Positive Flows
**Market**: `will-the-democrats-win-the-ohio-senate-race-in-2026`  
**Trading Period**: November 8-19, 2025 (12 days)  
**Total Trades**: 15 trades

![Ohio Senate Market - Log Scale](user_plots/segment_net_flow/will-the-democrats-win-the-ohio-senate-race-in-2026.png)

**Key Observations:**
- All segments show only positive daily net flows (all buying, no selling)
- Log scale automatically applied to better visualize segment differences
- Shows how different segments participate at different scales

**Pattern Analysis:**
- All segments are net buyers throughout the trading period
- Large differences in scale between segments (Small: $10-20, Medium: $138-458, Large: $21)
- Log scale makes it possible to see all segment patterns clearly

**Insight**: This market demonstrates the value of log scale - when all segments are net buyers but at vastly different scales, log scale allows us to see the patterns in Small and Medium segments that would be invisible on a linear scale dominated by Large segment activity. This helps understand user-level behavior across all segments.

## Key Insights Across Markets

### Segment Behavior Patterns

1. **Large Segment**:
   - Often drives major price movements with large daily flows
   - Can show dramatic swings (buying one day, selling the next)
   - Typically fewer trading days but larger impact per day
   - May indicate sophisticated trading strategies or position management

2. **Medium Segment**:
   - Most consistent participation across markets
   - Often provides liquidity with steady daily flows
   - Shows more balanced buy/sell activity
   - Represents the "middle class" of traders

3. **Small Segment**:
   - Consistent small positive flows in most markets
   - Lower volume but steady participation
   - Often net buyers, suggesting retail investor behavior
   - May indicate buy-and-hold strategies

### Market Characteristics

1. **High-Volume Markets** (e.g., Senate Majority Leader):
   - Dominated by Large segment activity
   - Extreme daily swings
   - High frequency trading patterns

2. **Balanced Markets** (e.g., State Senate Elections):
   - All segments participate more evenly
   - More stable daily flows
   - Broader market participation

3. **Low-Volume Markets**:
   - Sporadic activity
   - Often only one or two segments active
   - Less predictable patterns

### Trading Timeline Patterns

- **Early Days**: Often see initial position establishment
- **Mid-Period**: Peak activity with all segments trading
- **Late Period**: Activity typically declines, may see profit-taking
- **End Day**: Often minimal activity (market resolution)

## Statistics

- **Total Markets Analyzed**: 66
- **Total Plots Generated**: 66
- **Total CSV Files Generated**: 66
- **Date Range**: June 2024 - November 2025

## File Locations

All per-market plots and data are located in:
```
user_plots/
  segment_net_flow/          # PNG plots for each market
  segment_daily_net_flow/    # CSV data for each market
```

## Usage

To regenerate all per-market plots:

```bash
python3 per_market_segment_net_flow.py
```

The script processes all markets and generates individual plots showing daily net flow patterns for each segment within each market's timeline.

## Differences from Aggregate Plot

| Feature | Aggregate Plot | Per-Market Plots |
|---------|---------------|------------------|
| **Scope** | All markets combined | Individual markets |
| **Y-axis** | Cumulative net flow | Daily net flow |
| **Timeline** | Single combined timeline | Market-specific timeline |
| **Purpose** | Overall segment behavior | Market-specific patterns |
| **Use Case** | Understanding aggregate trends | Analyzing individual market dynamics |

## Interpretation Guide

### Reading the Plots

1. **Positive Daily Net Flow**: More buying than selling that day
   - Segment is accumulating positions
   - May indicate bullish sentiment

2. **Negative Daily Net Flow**: More selling than buying that day
   - Segment is reducing positions
   - May indicate bearish sentiment or profit-taking

3. **Zero Crossings**: Days where net flow changes direction
   - May indicate sentiment shifts
   - Could signal position adjustments

4. **Segment Divergence**: When segments move in opposite directions
   - Large selling while Small/Medium buying: Possible profit-taking by whales
   - Small/Medium selling while Large buying: Possible accumulation by institutions

### Market Analysis Workflow

1. **Identify Market Type**: High-volume vs. balanced vs. low-volume
2. **Analyze Segment Participation**: Which segments are active?
3. **Examine Daily Patterns**: Are there clear trends or volatility?
4. **Look for Divergences**: Do segments move together or apart?
5. **Timeline Analysis**: How does activity change over the market's lifetime?

## Conclusion

Per-market segment-wise daily net flow analysis provides granular insights into how different user segments behave within specific markets. This allows for:
- Market-specific pattern identification
- Segment behavior comparison within markets
- Timeline analysis of trading activity
- Understanding of market dynamics at a detailed level

Each market tells its own story through the daily net flow patterns of its participating segments.

