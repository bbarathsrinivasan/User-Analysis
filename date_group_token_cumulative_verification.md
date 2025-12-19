# Date Group Token Cumulative Values Verification

## User: 0xa58d4f278d7953cd38eeb929f7e242bfc7c0b9b8

This document provides step-by-step manual verification of all cumulative calculations in `date_group_token.csv`, verifying each row as a human would.

---

## Row 1: Date 2025-10-14

### Input Values
- **yes_value**: 172.86
- **no_value**: 369.52275
- **net_yes**: 2400.0
- **net_no**: 4742.35

### Step 1: Calculate total_token
```
total_token = net_yes + net_no
total_token = 2400.0 + 4742.35
total_token = 7142.35
```
✅ **Verified**: Matches CSV value of 7142.35

### Step 2: Calculate total_value
```
total_value = yes_value + no_value
total_value = 172.86 + 369.52275
total_value = 542.38275
```
✅ **Verified**: Matches CSV value of 542.38275

### Step 3: Calculate Cumulative Values (First Row - No Carry Forward)
Since this is the first row, cumulative values equal the current day's values:

```
cumulative_yes_value = yes_value = 172.86
cumulative_no_value = no_value = 369.52275
cumulative_net_yes = net_yes = 2400.0
cumulative_net_no = net_no = 4742.35
cumulative_total_token = total_token = 7142.35
cumulative_total_value = total_value = 542.38275
```

✅ **All Verified**: All cumulative values match CSV values

---

## Row 2: Date 2025-10-19

### Input Values
- **yes_value**: 0.0
- **no_value**: -378.4983
- **net_yes**: 0.0
- **net_no**: -667.38

### Step 1: Calculate total_token
```
total_token = net_yes + net_no
total_token = 0.0 + (-667.38)
total_token = -667.38
```
✅ **Verified**: Matches CSV value of -667.38

### Step 2: Calculate total_value
```
total_value = yes_value + no_value
total_value = 0.0 + (-378.4983)
total_value = -378.4983
```
✅ **Verified**: Matches CSV value of -378.4983

### Step 3: Calculate Cumulative Values (Carry Forward from Row 1)

#### cumulative_yes_value
```
cumulative_yes_value = previous cumulative_yes_value + current yes_value
cumulative_yes_value = 172.86 + 0.0
cumulative_yes_value = 172.86
```
✅ **Verified**: Matches CSV value of 172.86

#### cumulative_no_value
```
cumulative_no_value = previous cumulative_no_value + current no_value
cumulative_no_value = 369.52275 + (-378.4983)
cumulative_no_value = -8.97555
```
✅ **Verified**: Matches CSV value of -8.97555

#### cumulative_net_yes
```
cumulative_net_yes = previous cumulative_net_yes + current net_yes
cumulative_net_yes = 2400.0 + 0.0
cumulative_net_yes = 2400.0
```
✅ **Verified**: Matches CSV value of 2400.0

#### cumulative_net_no
```
cumulative_net_no = previous cumulative_net_no + current net_no
cumulative_net_no = 4742.35 + (-667.38)
cumulative_net_no = 4074.97
```
✅ **Verified**: Matches CSV value of 4074.97

#### cumulative_total_token
```
cumulative_total_token = previous cumulative_total_token + current total_token
cumulative_total_token = 7142.35 + (-667.38)
cumulative_total_token = 6474.97
```
✅ **Verified**: Matches CSV value of 6474.97

#### cumulative_total_value
```
cumulative_total_value = previous cumulative_total_value + current total_value
cumulative_total_value = 542.38275 + (-378.4983)
cumulative_total_value = 163.88445
```
✅ **Verified**: Matches CSV value of 163.88445

---

## Row 3: Date 2025-11-14

### Input Values
- **yes_value**: 0.0
- **no_value**: -2.30685
- **net_yes**: 0.0
- **net_no**: -21.97

### Step 1: Calculate total_token
```
total_token = net_yes + net_no
total_token = 0.0 + (-21.97)
total_token = -21.97
```
✅ **Verified**: Matches CSV value of -21.97

### Step 2: Calculate total_value
```
total_value = yes_value + no_value
total_value = 0.0 + (-2.30685)
total_value = -2.30685
```
✅ **Verified**: Matches CSV value of -2.30685

### Step 3: Calculate Cumulative Values (Carry Forward from Row 2)

#### cumulative_yes_value
```
cumulative_yes_value = previous cumulative_yes_value + current yes_value
cumulative_yes_value = 172.86 + 0.0
cumulative_yes_value = 172.86
```
✅ **Verified**: Matches CSV value of 172.86

#### cumulative_no_value
```
cumulative_no_value = previous cumulative_no_value + current no_value
cumulative_no_value = -8.97555 + (-2.30685)
cumulative_no_value = -11.28240
```
✅ **Verified**: Matches CSV value of -11.28240

#### cumulative_net_yes
```
cumulative_net_yes = previous cumulative_net_yes + current net_yes
cumulative_net_yes = 2400.0 + 0.0
cumulative_net_yes = 2400.0
```
✅ **Verified**: Matches CSV value of 2400.0

#### cumulative_net_no
```
cumulative_net_no = previous cumulative_net_no + current net_no
cumulative_net_no = 4074.97 + (-21.97)
cumulative_net_no = 4053.0
```
✅ **Verified**: Matches CSV value of 4053.0

#### cumulative_total_token
```
cumulative_total_token = previous cumulative_total_token + current total_token
cumulative_total_token = 6474.97 + (-21.97)
cumulative_total_token = 6453.0
```
✅ **Verified**: Matches CSV value of 6453.0

#### cumulative_total_value
```
cumulative_total_value = previous cumulative_total_value + current total_value
cumulative_total_value = 163.88445 + (-2.30685)
cumulative_total_value = 161.57760
```
✅ **Verified**: Matches CSV value of 161.57760

---

## Summary Table

| Date | total_token | total_value | cumulative_total_token | cumulative_total_value |
|------|-------------|-------------|------------------------|------------------------|
| 2025-10-14 | 7142.35 | 542.38275 | 7142.35 | 542.38275 |
| 2025-10-19 | -667.38 | -378.4983 | 6474.97 | 163.88445 |
| 2025-11-14 | -21.97 | -2.30685 | 6453.0 | 161.57760 |

---

## Calculation Rules Summary

1. **total_token** = `net_yes + net_no` (calculated for each row)
2. **total_value** = `yes_value + no_value` (calculated for each row)
3. **cumulative_yes_value** = Sum of all `yes_value` from first row to current row
4. **cumulative_no_value** = Sum of all `no_value` from first row to current row
5. **cumulative_net_yes** = Sum of all `net_yes` from first row to current row
6. **cumulative_net_no** = Sum of all `net_no` from first row to current row
7. **cumulative_total_token** = Sum of all `total_token` from first row to current row
8. **cumulative_total_value** = Sum of all `total_value` from first row to current row

---

## Verification Status

✅ **All calculations verified and match the generated `date_group_token.csv` file**

All cumulative values correctly carry forward from previous days, and all totals are calculated correctly for each row.
