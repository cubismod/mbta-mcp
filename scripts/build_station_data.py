#!/usr/bin/env python3
"""
Script to build static station data for major MBTA subway and commuter rail stations.

This script fetches all stops from the MBTA API and filters for major transit stations
(subway, light rail, commuter rail) with coordinates, creating a JSON file that can be
used to avoid API rate limits during trip planning.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path to import mbta_mcp
sys.path.append(str(Path(__file__).parent.parent))

from mbta_mcp.extended_client import ExtendedMBTAClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_major_stations() -> dict[str, Any]:
    """Fetch major transit stations using route type filters."""
    
    stations = {
        "rapid_transit": [],  # Subway/Light Rail stations
        "commuter_rail": [],  # Commuter Rail stations
        "metadata": {
            "generated_at": None,
            "total_stations": 0,
            "description": "Major MBTA transit stations with coordinates"
        }
    }
    
    async with ExtendedMBTAClient() as client:
        # Route types: 0=Light Rail, 1=Subway, 2=Commuter Rail, 3=Bus, 4=Ferry
        route_types = [
            (0, "Light Rail"),
            (1, "Subway"), 
            (2, "Commuter Rail")
        ]
        
        processed_stations = set()  # Avoid duplicates
        
        for route_type, type_name in route_types:
            logger.info(f"Fetching {type_name} stations (route_type={route_type})...")
            
            try:
                # Use filter[route_type] to get all stations for this transit type
                stops_result = await client._request("/stops", {
                    "page[limit]": 175,
                    "filter[route_type]": route_type,
                })
                
                if not stops_result.get("data"):
                    logger.warning(f"No {type_name} stations found")
                    continue
                    
                logger.info(f"Found {len(stops_result['data'])} {type_name} stations")
                
                for stop in stops_result["data"]:
                    stop_id = stop["id"]
                    name = stop["attributes"]["name"]
                    lat = stop["attributes"]["latitude"]
                    lon = stop["attributes"]["longitude"]
                    municipality = stop["attributes"].get("municipality", "")
                    description = stop["attributes"].get("description", "")
                    location_type = stop["attributes"]["location_type"]
                    
                    # Skip if already processed or no coordinates
                    if stop_id in processed_stations or not lat or not lon:
                        continue
                    
                    station_entry = {
                        "id": stop_id,
                        "name": name,
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "municipality": municipality,
                        "description": description,
                        "location_type": location_type,
                        "route_type": route_type,
                        "type_name": type_name
                    }
                    
                    # Categorize by route type
                    if route_type in [0, 1]:  # Light Rail or Subway
                        stations["rapid_transit"].append(station_entry)
                    elif route_type == 2:  # Commuter Rail
                        stations["commuter_rail"].append(station_entry)
                    
                    processed_stations.add(stop_id)
                    logger.info(f"Added {type_name}: {name}")
                
            except Exception as e:
                logger.error(f"Failed to fetch {type_name} stations: {e}")
                continue
    
    # Update metadata
    from datetime import datetime, UTC
    stations["metadata"]["generated_at"] = datetime.now(UTC).isoformat()
    stations["metadata"]["total_stations"] = len(stations["rapid_transit"]) + len(stations["commuter_rail"])
    
    # Sort stations by name for easier reading
    stations["rapid_transit"].sort(key=lambda x: x["name"])
    stations["commuter_rail"].sort(key=lambda x: x["name"])
    
    logger.info(f"Collected {len(stations['rapid_transit'])} rapid transit stations")
    logger.info(f"Collected {len(stations['commuter_rail'])} commuter rail stations")
    
    return stations


async def main():
    """Main function to fetch stations and save to JSON file."""
    
    try:
        logger.info("Starting station data collection...")
        stations = await fetch_major_stations()
        
        # Save to JSON file
        output_path = Path(__file__).parent.parent / "mbta_mcp" / "data" / "major_stations.json"
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(stations, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Station data saved to {output_path}")
        logger.info(f"Total stations: {stations['metadata']['total_stations']}")
        
        # Print summary
        print("\n=== MBTA Station Data Collection Summary ===")
        print(f"Rapid Transit Stations: {len(stations['rapid_transit'])}")
        print(f"Commuter Rail Stations: {len(stations['commuter_rail'])}")
        print(f"Total Stations: {stations['metadata']['total_stations']}")
        print(f"Output file: {output_path}")
        
        # Show some examples
        if stations["rapid_transit"]:
            print(f"\nExample Rapid Transit Stations:")
            for station in stations["rapid_transit"][:10]:
                print(f"  - {station['name']} [{station['type_name']}] ({station['latitude']}, {station['longitude']})")
        
        if stations["commuter_rail"]:
            print(f"\nExample Commuter Rail Stations:")
            for station in stations["commuter_rail"][:5]:
                print(f"  - {station['name']} [{station['type_name']}] ({station['latitude']}, {station['longitude']})")
                
    except Exception as e:
        logger.error(f"Failed to build station data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())