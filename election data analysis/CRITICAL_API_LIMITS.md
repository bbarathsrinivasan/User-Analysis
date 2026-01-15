# CRITICAL: Polymarket API Limits (Updated Aug 2025)

## ⚠️ IMPORTANT API RESTRICTIONS

As of **August 26, 2025**, Polymarket significantly reduced the limits on their `/trades` endpoint:

### **Official Limits:**
1. **Maximum `limit` parameter: 500** (down from 1000)
2. **Maximum `offset` parameter: 1,000** (NEW RESTRICTION!)
3. **Rate limit: 200 requests per 10 seconds** (up from 75)

**Source:** [Polymarket Changelog](https://docs.polymarket.com/changelog/changelog)

## 🚨 The Offset Problem

### **Without Time-Based Pagination:**
```
offset=0    → Get trades 0-499 (500 trades)
offset=500  → Get trades 500-999 (500 trades)  
offset=1000 → Get trades 1000-1499 (500 trades)
offset=1500 → ❌ API ERROR: offset exceeds maximum of 1,000
```

**Result:** You can only get the **first 1,500 trades** using standard offset pagination!

For markets with millions of trades, this is completely inadequate.

## ✅ The Solution: Time-Based Pagination

Instead of using `offset`, we use the `before` parameter with timestamps:

### **How It Works:**
1. Fetch first batch (newest 500 trades)
2. Get timestamp of oldest trade in batch
3. Next request: `before=<oldest_timestamp>`
4. Repeat until no more trades

### **Example:**
```
Request 1: GET /trades?market=0x123...&limit=500
  → Returns trades 1-500 (newest first)
  → Oldest trade timestamp: 1731129668

Request 2: GET /trades?market=0x123...&limit=500&before=1731129668
  → Returns trades 501-1000 (before that timestamp)
  → Oldest trade timestamp: 1730974556

Request 3: GET /trades?market=0x123...&limit=500&before=1730974556
  → Returns trades 1001-1500
  → And so on...
```

**Result:** Can fetch **ALL trades** regardless of total count! 🎉

## Implementation Status

### ✅ Updated in `collectors/dataCollectionScript.py`:

1. **Rate limiter updated:**
   ```python
   trades_limiter = RateLimiter(200, 10.0)  # 200 req/10s
   ```

2. **Batch size corrected:**
   ```python
   limit: int = 500,  # API max is 500
   ```

3. **Time-based pagination implemented:**
   ```python
   if before_timestamp is not None:
       params["before"] = before_timestamp
   ```

## Performance Impact

### With Time-Based Pagination:
For 9 million trades at 500 per request:

**API Calls:** 18,000 (9M / 500)
**Rate Limit:** 200 requests / 10 seconds
**Minimum Time:** 18,000 / 200 × 10s = **900 seconds = 15 minutes**

**Note:** Actual time will be longer due to:
- Network latency
- API response time
- Retry logic

**Realistic estimate:** ~20-30 minutes for 9M trades

### Comparison:

| Method | Limit | Trades Accessible | API Calls (9M trades) | Est. Time |
|--------|-------|-------------------|----------------------|-----------|
| **Offset only** | 500 | First 1,500 ❌ | N/A | N/A |
| **Time-based** | 500 | ALL ✅ | 18,000 | ~20-30 min |
| **Old (100)** | 100 | ALL | 90,000 | ~5.5 hours |

## Testing the Fix

### Quick Test (3 batches):
```bash
python test_fetch.py
```

**Look for:**
- Batch size = 500 (not 1000, not 100)
- "before=" in pagination info (shows time-based pagination working)
- Successfully fetches all 3 batches

### Full Fetch:
```bash
python fetch_trades.py
```

**Expected output:**
```
[fetch_trades] condition_id=0x1cf5bd0d52535a93... | page=1 | total_trades=500 | batch_size=500 | offset=0
[fetch_trades] condition_id=0x1cf5bd0d52535a93... | page=2 | total_trades=1,000 | batch_size=500 | offset=500
[fetch_trades] condition_id=0x1cf5bd0d52535a93... | page=3 | total_trades=1,500 | batch_size=500 | offset=1000
[fetch_trades] condition_id=0x1cf5bd0d52535a93... | page=4 | total_trades=2,000 | batch_size=500 | before=1731129668
[fetch_trades] condition_id=0x1cf5bd0d52535a93... | page=5 | total_trades=2,500 | batch_size=500 | before=1730974556
...
[fetch_trades] condition_id=0x1cf5bd0d52535a93... | COMPLETED | total_pages=17930 | total_trades=8,964,900
```

**Key indicators:**
- First 3 pages use `offset=` (0, 500, 1000)
- Page 4+ use `before=<timestamp>` (time-based pagination)
- Successfully fetches ALL trades, not just first 1,500

## Troubleshooting

### If you only get 1,500 trades:
- Time-based pagination is NOT working
- Check that `before` parameter is being extracted from batch
- Verify trades have `timestamp` field

### If you get "offset exceeds maximum" error:
- Old code is still being used
- Check `collectors/dataCollectionScript.py` has the updated version
- Restart Python interpreter

### If you get rate limited (429 errors):
- Rate limiter might not be working
- Check it's set to 200 req/10s (not 75)
- Add manual delays if needed

## References

- [Polymarket Changelog - Aug 2025 Update](https://docs.polymarket.com/changelog/changelog)
- [Polymarket API Rate Limits](https://docs.polymarket.com/quickstart/introduction/rate-limits)
- [Polymarket Data API Documentation](https://docs.polymarket.com/)

## Summary

**The Problem:** Offset limited to 1,000 = only 1,500 trades accessible

**The Solution:** Time-based pagination with `before` parameter = ALL trades accessible

**The Result:** Can now fetch 9 million trades in ~20-30 minutes (not 5.5 hours)

---

**Last Updated:** 2026-01-12
**API Limits Valid As Of:** August 26, 2025
