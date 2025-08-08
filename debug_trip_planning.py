#!/usr/bin/env python3
"""Debug script for trip planning step by step."""

import asyncio
import logging

from mbta_mcp.extended_client import ExtendedMBTAClient

logging.basicConfig(level=logging.INFO)

async def debug_trip_planning():
    async with ExtendedMBTAClient() as client:
        # Test coordinates for Kendall Square to Copley
        kendall_lat, kendall_lon = 42.3623, -71.0952
        copley_lat, copley_lon = 42.3505, -71.0845
        
        print("=== DEBUGGING TRIP PLANNING ===")
        print(f"Origin: {kendall_lat}, {kendall_lon}")
        print(f"Destination: {copley_lat}, {copley_lon}")
        
        # Step 1: Get nearby stops
        print("\n1. Finding nearby origin stops...")
        origin_stops = await client._find_nearby_transit_stops(
            kendall_lat, kendall_lon, 800, 5
        )
        
        print(f"Found {len(origin_stops.get('data', []))} origin stops:")
        for stop in origin_stops.get("data", []):
            stop_id = stop["id"]
            name = stop["attributes"]["name"]
            from_static = stop.get("_from_static_data", False)
            print(f"  - {stop_id}: {name} {'(static)' if from_static else '(API)'}")
            
        print("\n2. Finding nearby destination stops...")
        dest_stops = await client._find_nearby_transit_stops(
            copley_lat, copley_lon, 800, 5
        )
        
        print(f"Found {len(dest_stops.get('data', []))} destination stops:")
        for stop in dest_stops.get("data", []):
            stop_id = stop["id"]
            name = stop["attributes"]["name"]
            from_static = stop.get("_from_static_data", False)
            print(f"  - {stop_id}: {name} {'(static)' if from_static else '(API)'}")
        
        # Step 2: Test getting predictions for first origin stop
        if origin_stops.get("data"):
            first_origin_stop = origin_stops["data"][0]
            stop_id = first_origin_stop["id"]
            print(f"\n3. Testing predictions for origin stop {stop_id}...")
            
            try:
                predictions = await client.get_predictions_for_stop(stop_id, page_limit=10)
                print(f"Found {len(predictions.get('data', []))} predictions for stop {stop_id}")
                
                if predictions.get("data"):
                    for pred in predictions["data"][:3]:  # Show first 3
                        dep_time = pred["attributes"].get("departure_time", "N/A")
                        route_id = pred.get("relationships", {}).get("route", {}).get("data", {}).get("id", "N/A")
                        print(f"  - Route {route_id}: departs {dep_time}")
                else:
                    print("  No predictions found!")
                    
                    # Try with parent station if this is a platform
                    relationships = first_origin_stop.get("relationships", {})
                    parent_station = relationships.get("parent_station", {}).get("data")
                    if parent_station:
                        parent_id = parent_station.get("id")
                        print(f"  Trying parent station {parent_id}...")
                        parent_predictions = await client.get_predictions_for_stop(parent_id, page_limit=10)
                        print(f"  Found {len(parent_predictions.get('data', []))} predictions for parent station")
                        
            except Exception as e:
                print(f"  Error getting predictions: {e}")

if __name__ == "__main__":
    asyncio.run(debug_trip_planning())