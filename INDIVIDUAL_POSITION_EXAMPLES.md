# Individual Position Calculation Examples

This document explains how individual YES and NO positions are calculated, with special focus on how **negative cumulative positions** (from selling more than buying) contribute to individual positions.

## Position Formulas

For each user in each market:

- **H_y** = `yes_cumulative_position` (cumulative YES tokens: buys - sells)
- **H_n** = `no_cumulative_position` (cumulative NO tokens: buys - sells)

**Individual YES Position:**
```
individual_yes_position = (H_y if H_y > 0) + (-H_n if H_n < 0)
```

**Individual NO Position:**
```
individual_no_position = (H_n if H_n > 0) + (-H_y if H_y < 0)
```

### Key Insight

When a user has a **negative cumulative position** (sold more than bought), that negative position contributes to the **opposite** token's individual position. This captures the user's effective exposure:

- A negative YES position (`H_y < 0`) means the user effectively has a NO position
- A negative NO position (`H_n < 0`) means the user effectively has a YES position

---

## Example 1: Negative YES Position Contributing to Individual NO Position

**User**: `0x71ed0bc95433cdf1be29f43219725fce9addd9eb`  
**Market**: `will-gallego-win-arizona-senate-election-by-3-or-more`

### Day-by-Day Breakdown

| day_offset | yes_daily_sell | yes_cumulative_position (H_y) | no_cumulative_position (H_n) | individual_yes_position | individual_no_position |
|------------|----------------|-------------------------------|------------------------------|-------------------------|------------------------|
| -14 | 314.45 | **-314.45** | 0.0 | 0.0 | **314.45** |
| -13 | 0.0 | **-314.45** | 974.76 | 0.0 | **1289.21** |
| 0 | 0.0 | **-314.45** | 5974.76 | 0.0 | **6289.21** |

### Calculation Details

**Day -14:**
- User sells 314.45 YES tokens (no prior YES position)
- `yes_cumulative_position (H_y) = -314.45` (negative!)
- `no_cumulative_position (H_n) = 0.0`
- **Individual YES**: `(H_y if H_y > 0) + (-H_n if H_n < 0) = 0 + 0 = 0`
- **Individual NO**: `(H_n if H_n > 0) + (-H_y if H_y < 0) = 0 + (-(-314.45)) = 314.45` ✓

**Day -13:**
- User buys 974.76 NO tokens
- `yes_cumulative_position (H_y) = -314.45` (still negative)
- `no_cumulative_position (H_n) = 974.76` (positive)
- **Individual YES**: `(H_y if H_y > 0) + (-H_n if H_n < 0) = 0 + 0 = 0`
- **Individual NO**: `(H_n if H_n > 0) + (-H_y if H_y < 0) = 974.76 + (-(-314.45)) = 974.76 + 314.45 = 1289.21` ✓

**Day 0 (Closing):**
- `yes_cumulative_position (H_y) = -314.45` (still negative)
- `no_cumulative_position (H_n) = 5974.76` (increased from additional NO buys)
- **Individual YES**: `0` (H_y is negative, H_n is positive)
- **Individual NO**: `5974.76 + 314.45 = 6289.21` ✓

### Interpretation

This user **sold YES tokens** they didn't own (short selling), creating a negative YES position. This negative position (`-314.45`) is effectively a **NO position** because:
- If YES wins, they lose 314.45 tokens
- If NO wins, they benefit from their NO position

The individual NO position correctly includes both:
1. Their actual NO holdings: `5974.76`
2. Their effective NO exposure from short YES: `314.45`
3. **Total individual NO position: `6289.21`**

---

## Example 2: Negative NO Position Contributing to Individual YES Position

**User**: `0x2bc8bbfd8d5c787380330f448463473dabd3b39b`  
**Market**: `will-gallego-win-arizona-senate-election-by-1-2`

### Day-by-Day Breakdown

| day_offset | yes_daily_buy | yes_daily_sell | yes_cumulative_position (H_y) | no_cumulative_position (H_n) | individual_yes_position | individual_no_position |
|------------|----------------|-----------------|-------------------------------|------------------------------|-------------------------|------------------------|
| -17 | 253.5 | 0.0 | 253.5 | 20.0 | 253.5 | 20.0 |
| -16 | 0.0 | 233.5 | 20.0 | 20.0 | 20.0 | 20.0 |

### Calculation Details

**Day -17:**
- User buys 253.5 YES tokens and 20.0 NO tokens
- `yes_cumulative_position (H_y) = 253.5` (positive)
- `no_cumulative_position (H_n) = 20.0` (positive)
- **Individual YES**: `253.5 + 0 = 253.5` ✓
- **Individual NO**: `20.0 + 0 = 20.0` ✓

**Day -16:**
- User sells 233.5 YES tokens (reducing YES position)
- `yes_cumulative_position (H_y) = 253.5 - 233.5 = 20.0` (still positive)
- `no_cumulative_position (H_n) = 20.0` (unchanged)
- **Individual YES**: `20.0 + 0 = 20.0` ✓
- **Individual NO**: `20.0 + 0 = 20.0` ✓

### Hypothetical: If User Sold More NO Tokens

If this user had sold 30 NO tokens instead of 20 (selling more than they bought):

- `no_cumulative_position (H_n) = 20.0 - 30.0 = -10.0` (negative!)
- **Individual YES**: `20.0 + (-(-10.0)) = 20.0 + 10.0 = 30.0` ✓
- **Individual NO**: `0 + 0 = 0` (H_n is negative, H_y is positive)

The negative NO position (`-10.0`) would contribute `10.0` to the individual YES position, correctly reflecting that shorting NO is equivalent to a YES position.

---

## Example 3: Both Positions Negative (Short Both Sides)

**Hypothetical Scenario:**

A user sells both YES and NO tokens without owning them:

| day_offset | yes_cumulative_position (H_y) | no_cumulative_position (H_n) | individual_yes_position | individual_no_position |
|------------|-------------------------------|------------------------------|-------------------------|------------------------|
| -5 | -100.0 | -50.0 | 50.0 | 100.0 |

### Calculation

- `H_y = -100.0` (negative)
- `H_n = -50.0` (negative)

**Individual YES:**
```
(H_y if H_y > 0) + (-H_n if H_n < 0)
= 0 + (-(-50.0))
= 0 + 50.0
= 50.0 ✓
```

**Individual NO:**
```
(H_n if H_n > 0) + (-H_y if H_y < 0)
= 0 + (-(-100.0))
= 0 + 100.0
= 100.0 ✓
```

### Interpretation

When both positions are negative:
- The negative NO position (`-50`) contributes `50` to individual YES
- The negative YES position (`-100`) contributes `100` to individual NO
- This correctly captures that shorting both sides creates exposure in both directions

---

## Example 4: Mixed Positive and Negative Positions

**Scenario:**

A user has a positive YES position but a negative NO position:

| day_offset | yes_cumulative_position (H_y) | no_cumulative_position (H_n) | individual_yes_position | individual_no_position |
|------------|-------------------------------|------------------------------|-------------------------|------------------------|
| -10 | 500.0 | -200.0 | 700.0 | 0.0 |

### Calculation

- `H_y = 500.0` (positive)
- `H_n = -200.0` (negative)

**Individual YES:**
```
(H_y if H_y > 0) + (-H_n if H_n < 0)
= 500.0 + (-(-200.0))
= 500.0 + 200.0
= 700.0 ✓
```

**Individual NO:**
```
(H_n if H_n > 0) + (-H_y if H_y < 0)
= 0 + 0
= 0.0 ✓
```

### Interpretation

- The user owns 500 YES tokens (long YES)
- The user has shorted 200 NO tokens (negative NO position)
- Shorting NO is equivalent to being long YES, so:
  - **Individual YES = 500 + 200 = 700** (total YES exposure)
  - **Individual NO = 0** (no net NO exposure)

---

## Summary Table: How Negative Positions Contribute

| H_y | H_n | individual_yes_position | individual_no_position | Explanation |
|-----|-----|-------------------------|------------------------|-------------|
| +100 | +50 | 100 | 50 | Both positive: straightforward |
| -100 | +50 | 0 | 150 | Negative YES contributes to NO |
| +100 | -50 | 150 | 0 | Negative NO contributes to YES |
| -100 | -50 | 50 | 100 | Both negative: each contributes to opposite |
| 0 | -50 | 50 | 0 | Only negative NO: contributes to YES |
| -50 | 0 | 0 | 50 | Only negative YES: contributes to NO |

### Key Takeaways

1. **Negative positions represent short sales** (selling tokens you don't own)
2. **Shorting one side is equivalent to being long the other side**
3. **Individual positions capture total effective exposure** in each direction
4. **The formulas correctly handle all combinations** of positive and negative positions

---

## Real-World Example from Data

From `segment_output/arizona-senate-election-margin-of-victory/will-gallego-win-arizona-senate-election-by-3-or-more/user_0x71ed0bc95433cdf1be29f43219725fce9addd9eb.csv`:

```csv
day_offset,yes_daily_sell,yes_cumulative_position,no_cumulative_position,H_y,H_n,individual_yes_position,individual_no_position
-14,314.45,-314.45,0.0,-314.45,0.0,0.0,314.45
-13,0.0,-314.45,974.76,-314.45,974.76,0.0,1289.21
0,0.0,-314.45,5974.76,-314.45,5974.76,0.0,6289.21
```

**Key observations:**
- User sold 314.45 YES tokens on day -14 (short sale)
- This creates `H_y = -314.45` (negative cumulative YES position)
- The negative YES position contributes `314.45` to `individual_no_position`
- As the user accumulates NO tokens (`H_n` increases), the individual NO position grows
- Final individual NO position (`6289.21`) = NO holdings (`5974.76`) + effective NO from short YES (`314.45`)

This demonstrates how **selling can create negative positions that contribute to individual positions**, correctly capturing the user's total market exposure.

