# Quick Reference Card

## ⚡ TL;DR

**Problem:** Script only fetched first 1,500 trades due to Polymarket API offset limit

**Solution:** Implemented time-based pagination with `before` parameter

**Result:** Can now fetch ALL trades (millions) in ~20-30 minutes ✅

---

## 🎯 Key Numbers

| Item | Value |
|------|-------|
| **API Max Limit** | 500 trades/request |
| **API Max Offset** | 1,000 (only 1,500 trades!) |
| **Rate Limit** | 200 requests / 10 seconds |
| **API Calls (9M trades)** | 18,000 |
| **Time Required** | ~20-30 minutes |

---

## 🚀 Quick Start

### Test (5 batches only):
```bash
python test_fetch.py
```

**Expected:** Batch size = 500, fetches 5 batches successfully

### Full Fetch:
```bash
python fetch_trades.py
```

**Expected:** ~20-30 min for 9M trades, shows `before=` in logs

---

## ✅ Success Indicators

1. Batch size = **500** (not 100, not 1000)
2. Fetches **more than 3 batches** (proves time-based pagination works)
3. Logs show **`before=<timestamp>`** after batch 3
4. **No "offset exceeds maximum"** errors
5. Fetches **ALL trades**, not stopping at 1,500

---

## ❌ Failure Indicators

| Symptom | Problem | Fix |
|---------|---------|-----|
| Batch size = 100 | Old limit | Update line 218 to `limit: int = 500` |
| Stops at 1,500 trades | No time-pagination | Check `before` parameter extraction |
| "offset exceeds maximum" | Old offset-based code | Update to time-based pagination |
| Batch size = 1000 | Wrong limit | Change to 500 (API max) |

---

## 📂 Key Files

- `collectors/dataCollectionScript.py` - Core pagination logic
- `fetch_trades.py` - Main script
- `test_fetch.py` - Quick test
- `FINAL_FIX_SUMMARY.md` - Complete documentation
- `CRITICAL_API_LIMITS.md` - API restrictions explained

---

## 🔧 Critical Code Locations

### Batch Size (line ~218):
```python
limit: int = 500,  # API max
```

### Rate Limiter (line ~161):
```python
trades_limiter = RateLimiter(200, 10.0)
```

### Time-Based Pagination (line ~230-245):
```python
if before_timestamp is not None:
    params["before"] = before_timestamp
```

---

## 📞 Troubleshooting

See detailed guides:
- `TROUBLESHOOTING.md` - Debugging steps
- `CRITICAL_API_LIMITS.md` - API restrictions
- `FINAL_FIX_SUMMARY.md` - Complete fix details

---

**Status:** READY TO USE ✅
**Last Updated:** 2026-01-12
