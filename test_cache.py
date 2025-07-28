"""Test script to demonstrate the caching functionality."""
"""Test script to demonstrate the caching functionality."""

import asyncio
import time

from mbta_mcp.client import MBTAClient
from mbta_mcp.extended_client import ExtendedMBTAClient


async def test_caching() -> None:
    """Test the caching functionality."""
    print("Testing MBTA API caching...")

    # Test with basic client
    async with MBTAClient(enable_cache=True) as client:
        print("\n1. Testing basic client caching:")

        # First request - should hit the API
        start_time = time.time()
        routes = await client.get_routes(page_limit=5)
        first_request_time = time.time() - start_time
        print(f"   First request took: {first_request_time:.3f}s")
        print(f"   Routes returned: {len(routes.get('data', []))}")

        # Second request - should hit the cache
        start_time = time.time()
        routes_cached = await client.get_routes(page_limit=5)
        second_request_time = time.time() - start_time
        print(f"   Second request took: {second_request_time:.3f}s")
        print(f"   Routes returned: {len(routes_cached.get('data', []))}")

        # Show cache stats
        stats = client.get_cache_stats()
        print(f"   Cache stats: {stats}")

        # Test cache invalidation
        client.invalidate_cache("/routes", {"page[limit]": 5})
        print("   Cache invalidated for routes")

        # Third request - should hit the API again
        start_time = time.time()
        await client.get_routes(page_limit=5)
        third_request_time = time.time() - start_time
        print(f"   Third request took: {third_request_time:.3f}s")

        # Clear cache
        client.clear_cache()
        print("   Cache cleared")

    # Test with extended client
    async with ExtendedMBTAClient(enable_cache=True) as extended_client:
        print("\n2. Testing extended client caching:")

        # Test external API caching
        start_time = time.time()
        amtrak_trains = await extended_client.get_amtrak_trains()
        first_amtrak_time = time.time() - start_time
        print(f"   First Amtrak request took: {first_amtrak_time:.3f}s")
        print(f"   Trains returned: {len(amtrak_trains)}")

        # Second request - should hit the cache
        start_time = time.time()
        amtrak_trains_cached = await extended_client.get_amtrak_trains()
        second_amtrak_time = time.time() - start_time
        print(f"   Second Amtrak request took: {second_amtrak_time:.3f}s")
        print(f"   Trains returned: {len(amtrak_trains_cached)}")

        # Show cache stats
        stats = extended_client.get_cache_stats()
        print(f"   Cache stats: {stats}")

    print("\n3. Testing cache disabled:")
    async with MBTAClient(enable_cache=False) as client_no_cache:
        start_time = time.time()
        routes = await client_no_cache.get_routes(page_limit=5)
        no_cache_time = time.time() - start_time
        print(f"   Request without cache took: {no_cache_time:.3f}s")

        stats = client_no_cache.get_cache_stats()
        print(f"   Cache stats: {stats}")


if __name__ == "__main__":
    asyncio.run(test_caching())
