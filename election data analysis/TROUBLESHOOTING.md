# Troubleshooting: Missing Trades in fetch_trades.py

## Common Issues When Not All Trades Are Fetched

### 1. **API Pagination Limits**
The Polymarket API typically limits the number of trades returned per request (commonly 1000 per page). If `iter_trades_batches()` doesn't implement pagination correctly, it might stop after a certain number of trades.

**Solution**: Check if the `polymarket_pipeline` package's `iter_trades_batches` function has a `limit` or `max_trades` parameter. The API endpoint typically uses:
- `limit` parameter (e.g., 1000 trades per request)
- `offset` or `cursor` for pagination

### 2. **API Rate Limiting**
Polymarket may rate-limit requests (e.g., 100 requests per minute). If too many requests are made too quickly, the API might return errors or incomplete data.

**Solution**: 
- Reduce the `concurrency` parameter (currently set to 1 by default)
- Add delays between requests in `iter_trades_batches`
- Implement exponential backoff for failed requests

### 3. **Silent Errors in Async Iteration**
Errors during the async iteration over `iter_trades_batches` might be caught and logged as warnings, but the script continues, resulting in incomplete data.

**Solution**: Check the logs for warnings like:
- "received empty batch"
- "error during batch iteration"
- "DB trades write failed"

### 4. **Missing Early Pagination Parameter**
The `iter_trades_batches` function might not be fetching historical trades properly. APIs often require:
- `startTime` / `endTime` parameters
- `before` / `after` cursors for time-based pagination

### 5. **API Endpoint Limitations**
Some Polymarket API endpoints have absolute limits (e.g., maximum 100,000 trades per market), after which historical data is not available via the API.

**Solution**: Use the Polymarket Subgraph or bulk data exports if available.

## Debugging Steps

### Step 1: Run with Enhanced Logging
The updated `fetch_trades.py` now includes:
- Batch count logging
- Empty batch warnings
- Progress logging every 10 batches

Run the script and check for:
```bash
python fetch_trades.py 2>&1 | tee fetch_debug.log
```

Look for patterns like:
- "completed with X batches" - if X is a round number (e.g., 100), it might indicate a hard limit
- "received empty batch" - might indicate the iterator stopped early

### Step 2: Check the polymarket_pipeline Source
If you installed `polymarket_pipeline` via pip, find its source:
```bash
python -c "import polymarket_pipeline; print(polymarket_pipeline.__file__)"
```

Then examine `collectors/dataCollectionScript.py` and look for:
- `iter_trades_batches` function definition
- `LIMIT` or `MAX_TRADES` constants
- Pagination logic

### Step 3: Compare with Expected Trade Count
Check the Polymarket website or API directly:
1. Go to the market page on Polymarket
2. Check the "Activity" or "Trades" section for the total trade count
3. Compare with what your script fetched

### Step 4: Test with a Smaller Market
Test with a market that has fewer trades to see if the entire dataset is fetched:
```python
event_slugs = ["test-market-with-few-trades"]
```

### Step 5: Check API Documentation
Review the Polymarket API documentation for:
- Endpoint: `/trades` or `/markets/{id}/trades`
- Pagination parameters
- Rate limits
- Maximum historical data availability

## Solutions

### Solution 1: Increase Timeout
Add timeout parameters to the aiohttp session:
```python
timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
async with aiohttp.ClientSession(timeout=timeout) as session:
```

### Solution 2: Implement Manual Pagination
If `iter_trades_batches` is limited, implement your own pagination:
```python
async def fetch_all_trades(session, condition_id):
    all_trades = []
    offset = 0
    limit = 1000
    while True:
        batch = await fetch_trades_batch(session, condition_id, offset, limit)
        if not batch:
            break
        all_trades.extend(batch)
        offset += limit
    return all_trades
```

### Solution 3: Use Alternative Data Sources
- **Polymarket Subgraph**: Use GraphQL queries to fetch complete historical data
- **On-chain Data**: Query the Polygon blockchain directly for trade events
- **Bulk Exports**: Contact Polymarket for bulk data exports

## Next Steps

1. Run the updated script with enhanced logging
2. Check the logs for the issues mentioned above
3. Investigate the `polymarket_pipeline` source code
4. If the issue persists, consider alternative data sources
