"""MBTA MCP Server implementation."""

import asyncio
import json
import logging
from typing import Any

import mcp.server.stdio
from dotenv import load_dotenv
from mcp import types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .extended_client import ExtendedMBTAClient

load_dotenv()

logger = logging.getLogger("mbta-mcp")

server: Server = Server("mbta-mcp")  # type: ignore[type-arg]


@server.list_tools()  # type: ignore[misc, no-untyped-call]
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
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
                        "description": "Filter by route type (0=Light Rail, 1=Subway, 2=Commuter Rail, 3=Bus, 4=Ferry)",  # noqa: E501
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
                        "description": "Filter by facility type (ELEVATOR, ESCALATOR, PARKING_AREA, etc.)",  # noqa: E501
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
    ]


@server.call_tool()  # type: ignore[misc]
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """Handle tool calls."""
    if arguments is None:
        arguments = {}

    try:
        client: ExtendedMBTAClient
        async with ExtendedMBTAClient() as client:
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
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.exception("Error in %s", name)
        return [types.TextContent(type="text", text=f"Error: {e!s}")]


async def main() -> None:
    """Main entry point for the server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
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


if __name__ == "__main__":
    asyncio.run(main())
