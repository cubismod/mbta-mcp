#!/usr/bin/env python3
"""Test script to debug trip planning API issues."""

import asyncio
import json
from mbta_mcp.extended_client import ExtendedMBTAClient

async def test_trip_planning() -> None:
    """Test the trip planning functionality."""
    async with ExtendedMBTAClient() as client:
        # Test coordinates for Davis Square to South Station
        origin_lat, origin_lon = 42.39674, -71.121815  # Davis Square
        dest_lat, dest_lon = 42.352271, -71.055242     # South Station
        
        print("Testing trip planning from Davis Square to South Station...")
        print(f"Origin: ({origin_lat}, {origin_lon})")
        print(f"Destination: ({dest_lat}, {dest_lon})")
        
        # Test finding nearby stops
        print("\n1. Testing _find_nearby_transit_stops for origin...")
        origin_stops = await client._find_nearby_transit_stops(
            origin_lat, origin_lon, 800, 10, False
        )
        print(f"Origin stops found: {len(origin_stops.get('data', []))}")
        for stop in origin_stops.get('data', [])[:3]:
            print(f"  - {stop.get('attributes', {}).get('name', 'Unknown')} ({stop.get('id', 'No ID')})")
        
        print("\n2. Testing _find_nearby_transit_stops for destination...")
        dest_stops = await client._find_nearby_transit_stops(
            dest_lat, dest_lon, 800, 10, False
        )
        print(f"Destination stops found: {len(dest_stops.get('data', []))}")
        for stop in dest_stops.get('data', [])[:3]:
            print(f"  - {stop.get('attributes', {}).get('name', 'Unknown')} ({stop.get('id', 'No ID')})")
        
        # Test getting predictions for Davis Square
        print("\n3. Testing predictions for Davis Square...")
        davis_stop_id = "70063"  # Davis Square Red Line
        predictions = await client.get_predictions_for_stop(davis_stop_id, page_limit=10)
        print(f"Predictions found: {len(predictions.get('data', []))}")
        
        # Test full trip planning
        print("\n4. Testing full trip planning...")
        result = await client.plan_trip(
            origin_lat, origin_lon, dest_lat, dest_lon,
            prefer_fewer_transfers=True
        )
        
        print(f"Trip planning result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_trip_planning()) 
