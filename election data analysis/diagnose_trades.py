"""
Diagnostic script to help identify why trades are not being fully fetched.

This script will:
1. Check the polymarket_pipeline installation and version
2. Inspect the iter_trades_batches function
3. Fetch a sample of trades with detailed logging
4. Compare against known trade counts (if available)
"""

import asyncio
import aiohttp
import logging
import sys
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)


def check_package_installation():
    """Check if polymarket_pipeline is installed or collectors folder exists."""
    try:
        import polymarket_pipeline
        logging.info("✓ polymarket_pipeline is installed")
        logging.info(f"  Location: {polymarket_pipeline.__file__}")
        if hasattr(polymarket_pipeline, "__version__"):
            logging.info(f"  Version: {polymarket_pipeline.__version__}")
        return True
    except ImportError:
        # Check for local collectors folder
        collectors_path = Path(__file__).parent / "collectors" / "dataCollectionScript.py"
        if collectors_path.exists():
            logging.info("✓ Local collectors folder found")
            logging.info(f"  Location: {collectors_path}")
            return True
        else:
            logging.error(f"✗ Neither polymarket_pipeline package nor local collectors folder found")
            return False


def inspect_iter_trades_batches():
    """Inspect the iter_trades_batches function."""
    try:
        # Try package import first
        try:
            from polymarket_pipeline.collectors import dataCollectionScript as dcs
        except ImportError:
            # Fallback to local import
            import importlib.util
            mod_path = Path(__file__).parent / "collectors" / "dataCollectionScript.py"
            spec = importlib.util.spec_from_file_location("dataCollectionScript", str(mod_path))
            if not spec or not spec.loader:
                raise ImportError("Unable to import dataCollectionScript")
            dcs = importlib.util.module_from_spec(spec)
            sys.modules["dataCollectionScript"] = dcs
            spec.loader.exec_module(dcs)
        
        if hasattr(dcs, "iter_trades_batches"):
            func = dcs.iter_trades_batches
            logging.info("✓ iter_trades_batches found")
            logging.info(f"  Function: {func}")
            
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            logging.info(f"  Signature: {sig}")
            
            # Get source code if available
            try:
                source = inspect.getsource(func)
                logging.info("  Source code preview (first 30 lines):")
                for i, line in enumerate(source.split("\n")[:30], 1):
                    logging.info(f"    {i:3d}: {line}")
                
                # Look for limit/pagination keywords
                keywords = ["limit", "offset", "cursor", "next_page", "pagination", "max"]
                found_keywords = [kw for kw in keywords if kw.lower() in source.lower()]
                if found_keywords:
                    logging.info(f"  Found pagination keywords: {found_keywords}")
                    
                    # Extract default values
                    import re
                    limit_match = re.search(r'limit:\s*int\s*=\s*(\d+)', source)
                    if limit_match:
                        logging.info(f"  Default limit (batch size): {limit_match.group(1)}")
                    
                    max_trades_match = re.search(r'max_trades:\s*.*?=\s*(\w+)', source)
                    if max_trades_match:
                        logging.info(f"  Default max_trades: {max_trades_match.group(1)}")
                else:
                    logging.warning("  No obvious pagination keywords found")
            except Exception as e:
                logging.warning(f"  Could not get source code: {e}")
            
            return True
        else:
            logging.error("✗ iter_trades_batches not found in dataCollectionScript")
            return False
    except Exception as e:
        logging.error(f"✗ Error inspecting iter_trades_batches: {e}")
        return False


async def test_fetch_trades(event_slug: str = "nevada-us-senate-election-winner"):
    """Test fetching trades for a sample market."""
    try:
        from polymarket_pipeline.collectors import dataCollectionScript as dcs
    except Exception:
        import importlib.util
        mod_path = Path(__file__).parent / "collectors" / "dataCollectionScript.py"
        spec = importlib.util.spec_from_file_location("dataCollectionScript", str(mod_path))
        if not spec or not spec.loader:
            raise ImportError("Unable to import dataCollectionScript")
        dcs = importlib.util.module_from_spec(spec)
        sys.modules["dataCollectionScript"] = dcs
        spec.loader.exec_module(dcs)
    
    logging.info(f"Testing trade fetch for event: {event_slug}")
    
    async with aiohttp.ClientSession() as session:
        try:
            event = await dcs.get_event_by_slug(session, event_slug)
            markets = event.get("markets", [])
            logging.info(f"✓ Event loaded with {len(markets)} markets")
            
            if not markets:
                logging.error("✗ No markets found in event")
                return
            
            # Test with first market
            market = markets[0]
            slug = market.get("slug")
            condition_id = market.get("conditionId")
            
            logging.info(f"\nTesting market: {slug}")
            logging.info(f"  Condition ID: {condition_id}")
            
            batch_count = 0
            total_trades = 0
            batch_sizes = []
            
            logging.info("Fetching batches...")
            async for batch in dcs.iter_trades_batches(session, condition_id):
                if not batch:
                    logging.warning(f"  Batch {batch_count + 1}: EMPTY")
                    continue
                
                batch_count += 1
                batch_size = len(batch)
                total_trades += batch_size
                batch_sizes.append(batch_size)
                
                if batch_count <= 5:
                    logging.info(f"  Batch {batch_count}: {batch_size} trades")
                elif batch_count % 10 == 0:
                    logging.info(f"  Batch {batch_count}: {batch_size} trades (total so far: {total_trades})")
            
            logging.info(f"\n✓ Fetch complete!")
            logging.info(f"  Total batches: {batch_count}")
            logging.info(f"  Total trades: {total_trades}")
            
            if batch_sizes:
                logging.info(f"  Batch sizes: min={min(batch_sizes)}, max={max(batch_sizes)}, avg={sum(batch_sizes)/len(batch_sizes):.1f}")
                
                # Check for suspicious patterns
                if batch_count > 0 and all(size == batch_sizes[0] for size in batch_sizes):
                    logging.warning("  ⚠️  All batches have the same size - might indicate a hard limit")
                
                if total_trades % 1000 == 0 or total_trades % 10000 == 0:
                    logging.warning(f"  ⚠️  Total trades ({total_trades}) is a round number - might indicate API limit")
            
            # Compare with CSV if exists
            csv_path = Path(__file__).parent / event_slug / "trades" / f"{slug}_trades.csv"
            if csv_path.exists():
                import subprocess
                result = subprocess.run(["wc", "-l", str(csv_path)], capture_output=True, text=True)
                csv_line_count = int(result.stdout.split()[0]) - 1  # Subtract header
                logging.info(f"\n  CSV file exists with {csv_line_count} trades")
                if csv_line_count != total_trades:
                    logging.warning(f"  ⚠️  Mismatch: Fetched {total_trades} but CSV has {csv_line_count}")
            
        except Exception as e:
            logging.error(f"✗ Error during test fetch: {e}", exc_info=True)


def check_api_parameters():
    """Check if there are any hardcoded API limits in the code."""
    logging.info("\nChecking for hardcoded limits...")
    
    # Look for common patterns in the local files
    patterns = [
        (r"limit\s*=\s*(\d+)", "Limit parameter"),
        (r"max.*trades\s*=\s*(\d+)", "Max trades"),
        (r"page.*size\s*=\s*(\d+)", "Page size"),
    ]
    
    import re
    try:
        # Try package import first
        try:
            from polymarket_pipeline.collectors import dataCollectionScript as dcs
        except ImportError:
            # Fallback to local import
            import importlib.util
            mod_path = Path(__file__).parent / "collectors" / "dataCollectionScript.py"
            spec = importlib.util.spec_from_file_location("dataCollectionScript", str(mod_path))
            if not spec or not spec.loader:
                raise ImportError("Unable to import dataCollectionScript")
            dcs = importlib.util.module_from_spec(spec)
            sys.modules["dataCollectionScript"] = dcs
            spec.loader.exec_module(dcs)
        
        import inspect
        source = inspect.getsource(dcs)
        
        for pattern, description in patterns:
            matches = re.findall(pattern, source, re.IGNORECASE)
            if matches:
                unique_values = sorted(set(matches))
                logging.info(f"  Found {description}: {unique_values}")
    except Exception as e:
        logging.warning(f"  Could not check for limits: {e}")


def main():
    """Run all diagnostics."""
    logging.info("=" * 80)
    logging.info("TRADE FETCH DIAGNOSTICS")
    logging.info("=" * 80)
    
    logging.info("\n1. Checking package installation...")
    if not check_package_installation():
        logging.error("\nCannot proceed without polymarket_pipeline. Please install it.")
        return
    
    logging.info("\n2. Inspecting iter_trades_batches function...")
    inspect_iter_trades_batches()
    
    logging.info("\n3. Checking for API parameters...")
    check_api_parameters()
    
    logging.info("\n4. Testing actual trade fetch...")
    asyncio.run(test_fetch_trades())
    
    logging.info("\n" + "=" * 80)
    logging.info("DIAGNOSTICS COMPLETE")
    logging.info("=" * 80)
    
    logging.info("\nNext steps:")
    logging.info("1. Review the output above for warnings (⚠️)")
    logging.info("2. Check if there are API limits or pagination issues")
    logging.info("3. If needed, modify iter_trades_batches to implement proper pagination")
    logging.info("4. See TROUBLESHOOTING.md for detailed solutions")


if __name__ == "__main__":
    main()
