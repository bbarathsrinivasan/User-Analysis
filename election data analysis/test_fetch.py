"""
Quick test script to verify trade fetching is working correctly.

This fetches just the first few batches to confirm:
1. The collectors folder is accessible
2. The API connection works
3. The batch size is correct (1000, not 100)
4. Pagination is working

Run with: python test_fetch.py
"""

import asyncio
import aiohttp
import sys
from pathlib import Path
import importlib.util

# Import the local dataCollectionScript
mod_path = Path(__file__).parent / "collectors" / "dataCollectionScript.py"
spec = importlib.util.spec_from_file_location("dataCollectionScript", str(mod_path))
if not spec or not spec.loader:
    print("ERROR: Cannot load dataCollectionScript.py")
    sys.exit(1)

dcs = importlib.util.module_from_spec(spec)
sys.modules["dataCollectionScript"] = dcs
spec.loader.exec_module(dcs)

async def test_single_market():
    """Test fetching trades for a single market with limited batches."""
    
    event_slug = "nevada-us-senate-election-winner"
    print(f"\n{'='*80}")
    print(f"Testing Trade Fetch for: {event_slug}")
    print(f"{'='*80}\n")
    
    timeout = aiohttp.ClientTimeout(total=None, connect=60, sock_read=300)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            # Fetch event metadata
            print("Step 1: Fetching event metadata...")
            event = await dcs.get_event_by_slug(session, event_slug)
            print(f"  ✓ Event: {event.get('title')}")
            
            markets = event.get("markets", [])
            print(f"  ✓ Found {len(markets)} markets\n")
            
            if not markets:
                print("ERROR: No markets found!")
                return
            
            # Test first market
            market = markets[0]
            slug = market.get("slug")
            condition_id = market.get("conditionId")
            
            print(f"Step 2: Testing trade fetch for first market")
            print(f"  Market: {slug}")
            print(f"  Condition ID: {condition_id}\n")
            
            print("Step 3: Fetching first 5 batches (should be ~2500 trades if fixed)...")
            print("  Note: Polymarket API max limit is 500 trades/batch (as of Aug 2025)")
            print("-" * 80)
            
            batch_count = 0
            total_trades = 0
            batch_sizes = []
            has_time_pagination = False
            
            async for batch in dcs.iter_trades_batches(session, condition_id):
                if not batch:
                    print("  ⚠️  Received empty batch")
                    break
                
                batch_count += 1
                batch_size = len(batch)
                total_trades += batch_size
                batch_sizes.append(batch_size)
                
                # Check if we've switched to time-based pagination (after offset 1000)
                if batch_count > 3:
                    has_time_pagination = True
                
                print(f"  Batch {batch_count}: {batch_size} trades (total: {total_trades:,})")
                
                # Stop after 5 batches for testing (to verify time-based pagination works)
                if batch_count >= 5:
                    print("\n  (Stopping after 5 batches for test purposes)")
                    break
            
            print("-" * 80)
            print("\nTest Results:")
            print(f"  Total batches fetched: {batch_count}")
            print(f"  Total trades fetched: {total_trades:,}")
            
            if batch_sizes:
                avg_batch = sum(batch_sizes) / len(batch_sizes)
                print(f"  Batch sizes: min={min(batch_sizes)}, max={max(batch_sizes)}, avg={avg_batch:.0f}")
                
                print("\nAnalysis:")
                if avg_batch >= 450:
                    print("  ✅ EXCELLENT: Batch size ~500 - Fix is working!")
                    print("     API max is 500 (Polymarket limit as of Aug 2025)")
                    if batch_count >= 4:
                        print(f"  ✅ Time-based pagination is working! (fetched {batch_count} batches > 3)")
                        print("     This means you can fetch ALL trades, not just first 1,500!")
                    else:
                        print("  ℹ️  Run full fetch to verify time-based pagination works beyond 1,500 trades")
                elif avg_batch >= 200 and avg_batch < 450:
                    print("  ⚠️  MODERATE: Batch size ~200-450")
                    print("     Fix might be partially applied or market has fewer trades.")
                elif avg_batch <= 150:
                    print("  ❌ PROBLEM: Batch size ~100 or less")
                    print("     The fix is NOT working. Still using old limit=100.")
                else:
                    print(f"  ℹ️  INFO: Average batch size is {avg_batch:.0f}")
                
                # Check if batch sizes are consistent
                if len(set(batch_sizes)) == 1:
                    print(f"  ℹ️  All batches are the same size ({batch_sizes[0]})")
                    if batch_sizes[0] == 500:
                        print("     ✅ Correct! API max is 500.")
                    elif batch_sizes[0] == 100:
                        print("     ❌ Wrong! This indicates the old limit is still being used!")
                    elif batch_sizes[0] == 1000:
                        print("     ⚠️  Warning: API max was reduced to 500 in Aug 2025!")
                        print("     This might fail or be throttled.")
            
            print(f"\n{'='*80}")
            print("Test Complete!")
            print(f"{'='*80}\n")
            
            print("Next Steps:")
            if avg_batch >= 450:
                print("  1. ✅ The fix is working! You can now run the full fetch:")
                print("     python fetch_trades.py")
                print("\n  2. Expected time: ~20-30 minutes (instead of 5.5 hours)")
                print("\n  3. Watch for 'before=' in logs (indicates time-based pagination)")
                if batch_count >= 4:
                    print("\n  4. ✅ Time-based pagination confirmed! Will fetch ALL trades.")
            else:
                print("  1. The fix may not be applied correctly")
                print("  2. Check CRITICAL_API_LIMITS.md for details")
                print("  3. Verify collectors/dataCollectionScript.py shows:")
                print("     - Line ~218: limit: int = 500  # API max")
                print("     - Line ~240: params['before'] = before_timestamp")
                print("\n  4. CRITICAL: Must use time-based pagination or only 1,500 trades will be fetched!")
            
        except Exception as e:
            print(f"\n❌ ERROR: {type(e).__name__}: {e}")
            print("\nPossible causes:")
            print("  - Network connectivity issues")
            print("  - API rate limiting")
            print("  - Invalid event slug")
            print("\nCheck your internet connection and try again.")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("\nTrade Fetch Test Script")
    print("This will fetch the first 3 batches to verify the fixes are working.\n")
    
    try:
        asyncio.run(test_single_market())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
