#!/usr/bin/env python3
"""Test script to verify static data loading and nearby station detection."""

import asyncio
import logging

from mbta_mcp.extended_client import ExtendedMBTAClient

logging.basicConfig(level=logging.INFO)

async def test_static_data():
    async with ExtendedMBTAClient() as client:
        # Test loading static data
        major_stations = await client._load_major_stations()
        print(f"Loaded {len(major_stations.get('rapid_transit', []))} rapid transit stations")
        print(f"Loaded {len(major_stations.get('commuter_rail', []))} commuter rail stations")
        
        # Test finding nearby stops for Kendall Square area
        kendall_lat, kendall_lon = 42.3623, -71.0952
        nearby_stops = await client._find_nearby_transit_stops(
            kendall_lat, kendall_lon, 800, 5
        )
        
        print(f"\nNearby stops for Kendall Square area ({kendall_lat}, {kendall_lon}):")
        for stop in nearby_stops.get("data", []):
            name = stop["attributes"]["name"]
            distance = stop.get("_distance_km", 0) * 1000
            from_static = stop.get("_from_static_data", False)
            print(f"  - {name}: {distance:.0f}m {'(from static data)' if from_static else '(from API)'}")
            
        # Test for Copley area
        copley_lat, copley_lon = 42.3505, -71.0845
        nearby_stops_copley = await client._find_nearby_transit_stops(
            copley_lat, copley_lon, 800, 5
        )
        
        print(f"\nNearby stops for Copley area ({copley_lat}, {copley_lon}):")
        for stop in nearby_stops_copley.get("data", []):
            name = stop["attributes"]["name"]
            distance = stop.get("_distance_km", 0) * 1000
            from_static = stop.get("_from_static_data", False)
            print(f"  - {name}: {distance:.0f}m {'(from static data)' if from_static else '(from API)'}")

if __name__ == "__main__":
    asyncio.run(test_static_data())