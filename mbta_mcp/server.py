"""MBTA MCP Server implementation."""

import asyncio
import json
import logging
import os
import sys
from typing import Any

import mcp.server.stdio
from dotenv import load_dotenv
from mcp import types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .extended_client import ExtendedMBTAClient

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger("mbta-mcp")

server: Server = Server("mbta-mcp")  # type: ignore[type-arg]


@server.list_tools()  # type: ignore[misc, no-untyped-call]
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    logger.info("Client requested list of available tools")
    tool_count = 30  # We have 30 MBTA tools (including 3 Amtrak tools + 6 list_all tools + 1 time-based schedule tool)
    logger.info("Returning %d MBTA API tools", tool_count)
    return [
        types.Tool(
            name="mbta_get_routes",
            description="Get MBTA routes. Optionally filter by route ID or type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "route_id": {
                        "type": "string",
                        "description": "Specific route ID to get",
                    },
                    "route_type": {
                        "type": "integer",
                        "description": "Filter by route type (0=Light Rail, 1=Subway, 2=Commuter Rail, 3=Bus, 4=Ferry)",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_get_stops",
            description="Get MBTA stops. Filter by stop ID, route, or location.",
            inputSchema={
                "type": "object",
                "properties": {
                    "stop_id": {
                        "type": "string",
                        "description": "Specific stop ID to get",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Filter stops by route ID",
                    },
                    "latitude": {
                        "type": "number",
                        "description": "Latitude for location-based search",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude for location-based search",
                    },
                    "radius": {
                        "type": "number",
                        "description": "Search radius in meters (used with lat/lng)",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_get_predictions",
            description="Get real-time predictions for MBTA services.",
            inputSchema={
                "type": "object",
                "properties": {
                    "stop_id": {
                        "type": "string",
                        "description": "Filter predictions by stop ID",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Filter predictions by route ID",
                    },
                    "trip_id": {
                        "type": "string",
                        "description": "Filter predictions by trip ID",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_get_schedules",
            description="Get scheduled MBTA service times.",
            inputSchema={
                "type": "object",
                "properties": {
                    "stop_id": {
                        "type": "string",
                        "description": "Filter schedules by stop ID",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Filter schedules by route ID",
                    },
                    "trip_id": {
                        "type": "string",
                        "description": "Filter schedules by trip ID",
                    },
                    "direction_id": {
                        "type": "integer",
                        "description": "Filter by direction (0 or 1)",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_get_trips",
            description="Get MBTA trip information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "string",
                        "description": "Specific trip ID to get",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Filter trips by route ID",
                    },
                    "direction_id": {
                        "type": "integer",
                        "description": "Filter by direction (0 or 1)",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_get_alerts",
            description="Get MBTA service alerts and disruptions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "alert_id": {
                        "type": "string",
                        "description": "Specific alert ID to get",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Filter alerts by route ID",
                    },
                    "stop_id": {
                        "type": "string",
                        "description": "Filter alerts by stop ID",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_get_vehicles",
            description="Get real-time MBTA vehicle positions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vehicle_id": {
                        "type": "string",
                        "description": "Specific vehicle ID to get",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Filter vehicles by route ID",
                    },
                    "trip_id": {
                        "type": "string",
                        "description": "Filter vehicles by trip ID",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_get_services",
            description="Get MBTA service definitions and calendars.",
            inputSchema={
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "Specific service ID to get",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_get_shapes",
            description="Get route shape/path information for mapping.",
            inputSchema={
                "type": "object",
                "properties": {
                    "shape_id": {
                        "type": "string",
                        "description": "Specific shape ID to get",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Filter shapes by route ID",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_get_facilities",
            description="Get facility information (elevators, escalators, parking).",
            inputSchema={
                "type": "object",
                "properties": {
                    "facility_id": {
                        "type": "string",
                        "description": "Specific facility ID to get",
                    },
                    "stop_id": {
                        "type": "string",
                        "description": "Filter facilities by stop ID",
                    },
                    "facility_type": {
                        "type": "string",
                        "description": "Filter by facility type (ELEVATOR, ESCALATOR, PARKING_AREA, etc.)",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_get_live_facilities",
            description="Get real-time facility status and outages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "facility_id": {
                        "type": "string",
                        "description": "Specific facility ID to get status for",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_search_stops",
            description="Search for stops by name or near a location.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for stop names",
                    },
                    "latitude": {
                        "type": "number",
                        "description": "Latitude for location-based search",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude for location-based search",
                    },
                    "radius": {
                        "type": "number",
                        "description": "Search radius in meters (default: 1000)",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="mbta_get_nearby_stops",
            description="Get stops near a specific location.",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude of the location",
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the location",
                    },
                    "radius": {
                        "type": "number",
                        "description": "Search radius in meters (default: 1000)",
                        "default": 1000,
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["latitude", "longitude"],
            },
        ),
        types.Tool(
            name="mbta_get_predictions_for_stop",
            description="Get all predictions for a specific stop.",
            inputSchema={
                "type": "object",
                "properties": {
                    "stop_id": {
                        "type": "string",
                        "description": "Stop ID to get predictions for",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Filter by specific route",
                    },
                    "direction_id": {
                        "type": "integer",
                        "description": "Filter by direction (0 or 1)",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["stop_id"],
            },
        ),
        types.Tool(
            name="mbta_get_vehicle_positions",
            description=(
                "Get real-time vehicle positions from external API. Returns GeoJSON "
                "data with vehicle locations, routes, status, and other real-time "
                "information."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="mbta_get_external_alerts",
            description=(
                "Get general alerts from external API. Returns real-time service "
                "alerts, delays, disruptions, and other service information."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="mbta_get_track_prediction",
            description=(
                "Get track prediction for a specific trip using IMT API. "
                "Predicts which track a train will use at a station."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "station_id": {
                        "type": "string",
                        "description": "Station ID where prediction is needed",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Route ID (e.g., CR-Providence)",
                    },
                    "trip_id": {
                        "type": "string",
                        "description": "Trip ID for the specific train",
                    },
                    "headsign": {
                        "type": "string",
                        "description": "Destination/headsign (e.g., South Station)",
                    },
                    "direction_id": {
                        "type": "integer",
                        "description": "Direction (0 or 1)",
                    },
                    "scheduled_time": {
                        "type": "string",
                        "description": "Scheduled departure/arrival time (ISO format)",
                    },
                },
                "required": [
                    "station_id",
                    "route_id",
                    "trip_id",
                    "headsign",
                    "direction_id",
                    "scheduled_time",
                ],
            },
        ),
        types.Tool(
            name="mbta_get_chained_track_predictions",
            description=(
                "Get multiple track predictions in a single request using IMT API. "
                "Useful for batch predictions of multiple trips."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "predictions": {
                        "type": "array",
                        "description": "Array of prediction requests",
                        "items": {
                            "type": "object",
                            "properties": {
                                "station_id": {"type": "string"},
                                "route_id": {"type": "string"},
                                "trip_id": {"type": "string"},
                                "headsign": {"type": "string"},
                                "direction_id": {"type": "integer"},
                                "scheduled_time": {"type": "string"},
                            },
                        },
                    },
                },
                "required": ["predictions"],
            },
        ),
        types.Tool(
            name="mbta_get_prediction_stats",
            description=(
                "Get prediction statistics and accuracy metrics for a station and route."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "station_id": {
                        "type": "string",
                        "description": "Station ID to get stats for",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Route ID to get stats for",
                    },
                },
                "required": ["station_id", "route_id"],
            },
        ),
        types.Tool(
            name="mbta_get_historical_assignments",
            description=(
                "Get historical track assignments for analysis using IMT API. "
                "Shows actual track assignments from past trips."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "station_id": {
                        "type": "string",
                        "description": "Station ID to get historical data for",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Route ID to get historical data for",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default: 30)",
                        "default": 30,
                    },
                },
                "required": ["station_id", "route_id"],
            },
        ),
        types.Tool(
            name="mbta_get_amtrak_trains",
            description=(
                "Get all tracked Amtrak trains from the Boston Amtrak Tracker API. "
                "Returns real-time train locations, routes, status, and other information."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="mbta_get_amtrak_trains_geojson",
            description=(
                "Get Amtrak trains as GeoJSON for mapping applications. "
                "Returns train data formatted as GeoJSON suitable for mapping."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="mbta_get_amtrak_health_status",
            description=(
                "Get health status of the Boston Amtrak Tracker API. "
                "Returns server health status and last data update time."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="mbta_list_all_alerts",
            description=(
                "List all MBTA alerts with optional fuzzy filtering. "
                "Returns all alerts without specific filters, with client-side fuzzy search."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional fuzzy search query to filter alerts by header or description",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_list_all_facilities",
            description=(
                "List all MBTA facilities with optional fuzzy filtering. "
                "Returns all facilities without specific filters, with client-side fuzzy search."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional fuzzy search query to filter facilities by name",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_list_all_lines",
            description=(
                "List all MBTA lines with optional fuzzy filtering. "
                "Returns all lines without specific filters, with client-side fuzzy search."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional fuzzy search query to filter lines by name",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_list_all_routes",
            description=(
                "List all MBTA routes with optional fuzzy filtering. "
                "Returns all routes without specific filters, with client-side fuzzy search."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional fuzzy search query to filter routes by name",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_list_all_services",
            description=(
                "List all MBTA services with optional fuzzy filtering. "
                "Returns all services without specific filters, with client-side fuzzy search."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional fuzzy search query to filter services by description",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_list_all_stops",
            description=(
                "List all MBTA stops with optional fuzzy filtering. "
                "Returns all stops without specific filters, with client-side fuzzy search."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional fuzzy search query to filter stops by name",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50,
                    },
                },
            },
        ),
        types.Tool(
            name="mbta_get_schedules_by_time",
            description=(
                "Get MBTA schedules filtered by specific times and dates. "
                "Use this to find transit schedules for particular time windows, dates, or specific trips."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Filter by service date (YYYY-MM-DD format)",
                    },
                    "min_time": {
                        "type": "string",
                        "description": "Filter schedules at or after this time (HH:MM format, use >24:00 for next day)",
                    },
                    "max_time": {
                        "type": "string",
                        "description": "Filter schedules at or before this time (HH:MM format)",
                    },
                    "route_id": {
                        "type": "string",
                        "description": "Filter by specific route ID",
                    },
                    "stop_id": {
                        "type": "string",
                        "description": "Filter by specific stop ID",
                    },
                    "trip_id": {
                        "type": "string",
                        "description": "Filter by specific trip ID",
                    },
                    "direction_id": {
                        "type": "integer",
                        "description": "Filter by direction (0 or 1)",
                    },
                    "page_limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10,
                    },
                },
            },
        ),
    ]


@server.call_tool()  # type: ignore[misc]
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Handle tool calls."""
    logger.info("Received tool call: %s", name)
    if arguments:
        logger.debug("Tool arguments: %s", arguments)

    if arguments is None:
        arguments = {}

    try:
        logger.info("Initializing MBTA client for %s", name)
        client: ExtendedMBTAClient
        async with ExtendedMBTAClient() as client:
            result: Any
            if name == "mbta_get_routes":
                result = await client.get_routes(
                    route_id=arguments.get("route_id"),
                    route_type=arguments.get("route_type"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_stops":
                result = await client.get_stops(
                    stop_id=arguments.get("stop_id"),
                    route_id=arguments.get("route_id"),
                    latitude=arguments.get("latitude"),
                    longitude=arguments.get("longitude"),
                    radius=arguments.get("radius"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_predictions":
                result = await client.get_predictions(
                    stop_id=arguments.get("stop_id"),
                    route_id=arguments.get("route_id"),
                    trip_id=arguments.get("trip_id"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_schedules":
                result = await client.get_schedules(
                    stop_id=arguments.get("stop_id"),
                    route_id=arguments.get("route_id"),
                    trip_id=arguments.get("trip_id"),
                    direction_id=arguments.get("direction_id"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_trips":
                result = await client.get_trips(
                    trip_id=arguments.get("trip_id"),
                    route_id=arguments.get("route_id"),
                    direction_id=arguments.get("direction_id"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_alerts":
                result = await client.get_alerts(
                    alert_id=arguments.get("alert_id"),
                    route_id=arguments.get("route_id"),
                    stop_id=arguments.get("stop_id"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_vehicles":
                result = await client.get_vehicles(
                    vehicle_id=arguments.get("vehicle_id"),
                    route_id=arguments.get("route_id"),
                    trip_id=arguments.get("trip_id"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_services":
                result = await client.get_services(
                    service_id=arguments.get("service_id"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_shapes":
                result = await client.get_shapes(
                    shape_id=arguments.get("shape_id"),
                    route_id=arguments.get("route_id"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_facilities":
                result = await client.get_facilities(
                    facility_id=arguments.get("facility_id"),
                    stop_id=arguments.get("stop_id"),
                    facility_type=arguments.get("facility_type"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_live_facilities":
                result = await client.get_live_facilities(
                    facility_id=arguments.get("facility_id"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_search_stops":
                result = await client.search_stops(
                    query=arguments["query"],
                    latitude=arguments.get("latitude"),
                    longitude=arguments.get("longitude"),
                    radius=arguments.get("radius"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_nearby_stops":
                result = await client.get_nearby_stops(
                    latitude=arguments["latitude"],
                    longitude=arguments["longitude"],
                    radius=arguments.get("radius", 1000),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_predictions_for_stop":
                result = await client.get_predictions_for_stop(
                    stop_id=arguments["stop_id"],
                    route_id=arguments.get("route_id"),
                    direction_id=arguments.get("direction_id"),
                    page_limit=arguments.get("page_limit", 10),
                )
            elif name == "mbta_get_vehicle_positions":
                result = await client.get_vehicle_positions()
            elif name == "mbta_get_external_alerts":
                result = await client.get_external_alerts()
            elif name == "mbta_get_track_prediction":
                result = await client.get_track_prediction(
                    station_id=arguments["station_id"],
                    route_id=arguments["route_id"],
                    trip_id=arguments["trip_id"],
                    headsign=arguments["headsign"],
                    direction_id=arguments["direction_id"],
                    scheduled_time=arguments["scheduled_time"],
                )
            elif name == "mbta_get_chained_track_predictions":
                result = await client.get_chained_track_predictions(
                    predictions=arguments["predictions"]
                )
            elif name == "mbta_get_prediction_stats":
                result = await client.get_prediction_stats(
                    station_id=arguments["station_id"],
                    route_id=arguments["route_id"],
                )
            elif name == "mbta_get_historical_assignments":
                result = await client.get_historical_assignments(
                    station_id=arguments["station_id"],
                    route_id=arguments["route_id"],
                    days=arguments.get("days", 30),
                )
            elif name == "mbta_get_amtrak_trains":
                result = await client.get_amtrak_trains()
            elif name == "mbta_get_amtrak_trains_geojson":
                result = await client.get_amtrak_trains_geojson()
            elif name == "mbta_get_amtrak_health_status":
                result = await client.get_amtrak_health_status()
            elif name == "mbta_list_all_alerts":
                result = await client.list_all_alerts(
                    query=arguments.get("query"),
                    max_results=arguments.get("max_results", 50),
                )
            elif name == "mbta_list_all_facilities":
                result = await client.list_all_facilities(
                    query=arguments.get("query"),
                    max_results=arguments.get("max_results", 50),
                )
            elif name == "mbta_list_all_lines":
                result = await client.list_all_lines(
                    query=arguments.get("query"),
                    max_results=arguments.get("max_results", 50),
                )
            elif name == "mbta_list_all_routes":
                result = await client.list_all_routes(
                    query=arguments.get("query"),
                    max_results=arguments.get("max_results", 50),
                )
            elif name == "mbta_list_all_services":
                result = await client.list_all_services(
                    query=arguments.get("query"),
                    max_results=arguments.get("max_results", 50),
                )
            elif name == "mbta_list_all_stops":
                result = await client.list_all_stops(
                    query=arguments.get("query"),
                    max_results=arguments.get("max_results", 50),
                )
            elif name == "mbta_get_schedules_by_time":
                result = await client.get_schedules_by_time(
                    date=arguments.get("date"),
                    min_time=arguments.get("min_time"),
                    max_time=arguments.get("max_time"),
                    route_id=arguments.get("route_id"),
                    stop_id=arguments.get("stop_id"),
                    trip_id=arguments.get("trip_id"),
                    direction_id=arguments.get("direction_id"),
                    page_limit=arguments.get("page_limit", 10),
                )
            else:
                raise ValueError(f"Unknown tool: {name}")

            logger.info("Successfully executed %s", name)
            response_size = len(json.dumps(result))
            logger.debug("Response size: %d characters", response_size)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.exception("Error executing %s", name)
        return [types.TextContent(type="text", text=f"Error: {e!s}")]


async def async_main() -> None:
    """Async main entry point for the server."""
    logger.info("🚇 MBTA MCP Server starting up...")

    # Check MBTA API key status
    api_key = os.getenv("MBTA_API_KEY")
    if api_key:
        logger.info("✓ MBTA API key found (length: %d)", len(api_key))
    else:
        logger.warning(
            "⚠ No MBTA API key configured (some endpoints may be rate-limited)"
        )

    logger.info("Starting MCP server on stdio...")

    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("✓ MCP server connected, waiting for client...")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="mbta-mcp",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested")
    except Exception:
        logger.exception("💥 Server error")
        raise
    finally:
        logger.info("🚇 MBTA MCP Server shutting down...")


def main() -> None:
    """Main entry point for the server (synchronous wrapper)."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
