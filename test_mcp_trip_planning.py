#!/usr/bin/env python3
"""Test script to simulate MCP server trip planning call."""

import asyncio
import json
import os
from dotenv import load_dotenv
from mbta_mcp.extended_client import ExtendedMBTAClient

# Load environment variables from .env file
load_dotenv()

async def test_mcp_trip_planning() -> None:
    """Test trip planning the same way the MCP server does."""
    # Check if API key is loaded
    api_key = os.getenv("MBTA_API_KEY")
    if not api_key:
        print("WARNING: MBTA_API_KEY not found in environment variables!")
        print("Make sure you have a .env file with MBTA_API_KEY=your_key_here")
        return
    
    print(f"API key loaded: {api_key[:10]}...")
    
    async with ExtendedMBTAClient() as client:
        # Test coordinates for Davis Square to South Station
        origin_lat, origin_lon = 42.39674, -71.121815  # Davis Square
        dest_lat, dest_lon = 42.352271, -71.055242     # South Station
        
        print("Testing MCP-style trip planning from Davis Square to South Station...")
        print(f"Origin: ({origin_lat}, {origin_lon})")
        print(f"Destination: ({dest_lat}, {dest_lon})")
        
        # Call plan_trip exactly like the MCP server does
        result = await client.plan_trip(
            origin_lat=origin_lat,
            origin_lon=origin_lon,
            dest_lat=dest_lat,
            dest_lon=dest_lon,
            departure_time=None,
            arrival_time=None,
            max_walk_distance=800,
            max_transfers=3,
            prefer_fewer_transfers=True,
            wheelchair_accessible=False,
        )
        
        print(f"\nTrip planning result type: {type(result)}")
        print(f"Trip planning result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        print(f"Trip planning result: {json.dumps(result, indent=2)}")
        
        # Check if the result is empty
        if isinstance(result, dict) and result.get("trip_options"):
            print(f"\nFound {len(result['trip_options'])} trip options!")
            for i, option in enumerate(result["trip_options"][:3]):
                print(f"Option {i+1}: {option.get('departure_time', 'Unknown')} - {option.get('arrival_time', 'Unknown')}")
        else:
            print("\nNo trip options found!")

if __name__ == "__main__":
    asyncio.run(test_mcp_trip_planning())
