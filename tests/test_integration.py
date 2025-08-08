"""Integration tests for MBTA MCP server."""

import asyncio
import json
import os
from unittest.mock import AsyncMock, patch

import pytest
from mcp import types

from mbta_mcp.extended_client import ExtendedMBTAClient
from mbta_mcp.server import handle_call_tool, handle_list_tools


class TestMCPServerIntegration:
    """Integration tests for the MCP server."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_expected_tools(self) -> None:
        """Test that all expected tools are registered."""
        tools = await handle_list_tools()

        assert len(tools) == 32, f"Expected 32 tools, got {len(tools)}"

        tool_names = {tool.name for tool in tools}

        # Core MBTA API tools based on actual server implementation
        expected_tools = {
            "mbta_get_alerts",
            "mbta_get_amtrak_health_status",
            "mbta_get_amtrak_trains",
            "mbta_get_amtrak_trains_geojson",
            "mbta_get_chained_track_predictions",
            "mbta_get_external_alerts",
            "mbta_get_facilities",
            "mbta_get_historical_assignments",
            "mbta_get_live_facilities",
            "mbta_get_nearby_stops",
            "mbta_get_prediction_stats",
            "mbta_get_predictions",
            "mbta_get_predictions_for_stop",
            "mbta_get_routes",
            "mbta_get_schedules",
            "mbta_get_schedules_by_time",
            "mbta_get_services",
            "mbta_get_shapes",
            "mbta_get_stops",
            "mbta_get_track_prediction",
            "mbta_get_trips",
            "mbta_get_vehicle_positions",
            "mbta_get_vehicles",
            "mbta_list_all_alerts",
            "mbta_list_all_facilities",
            "mbta_list_all_lines",
            "mbta_list_all_routes",
            "mbta_list_all_services",
            "mbta_list_all_stops",
            "mbta_search_stops",
            "mbta_plan_trip",
            "mbta_get_route_alternatives",
        }

        missing_tools = expected_tools - tool_names
        extra_tools = tool_names - expected_tools

        assert not missing_tools, f"Missing tools: {missing_tools}"
        assert not extra_tools, f"Unexpected extra tools: {extra_tools}"

    @pytest.mark.asyncio
    async def test_tool_schemas_are_valid(self) -> None:
        """Test that all tool schemas are valid JSON schemas."""
        tools = await handle_list_tools()

        for tool in tools:
            assert isinstance(tool.inputSchema, dict)
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"

            if "properties" in tool.inputSchema:
                assert isinstance(tool.inputSchema["properties"], dict)

    @pytest.mark.asyncio
    async def test_get_routes_without_api_key(self) -> None:
        """Test routes endpoint without API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = await handle_call_tool("mbta_get_routes", {"page_limit": 1})

            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)

            # Should either succeed or return a proper error message
            content = result[0].text
            assert isinstance(content, str)
            assert len(content) > 0

    @pytest.mark.asyncio
    async def test_get_routes_with_invalid_parameters(self) -> None:
        """Test routes endpoint with invalid parameters."""
        result = await handle_call_tool(
            "mbta_get_routes", {"route_type": 999, "page_limit": 1}
        )

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

    @pytest.mark.asyncio
    async def test_search_stops_functionality(self) -> None:
        """Test stop search functionality."""
        result = await handle_call_tool(
            "mbta_search_stops", {"query": "Park Street", "limit": 5}
        )

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        content = result[0].text
        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_invalid_tool_name_returns_error(self) -> None:
        """Test that invalid tool names return error messages."""
        result = await handle_call_tool("invalid_tool_name", {})

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Error:" in result[0].text
        assert "Unknown tool" in result[0].text

    @pytest.mark.asyncio
    async def test_client_error_handling(self) -> None:
        """Test that client errors are properly handled."""
        with patch("mbta_mcp.server.ExtendedMBTAClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get_routes.side_effect = Exception("Network error")
            mock_client_class.return_value = mock_client

            result = await handle_call_tool("mbta_get_routes", {})

            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)
            assert "Error:" in result[0].text

    @pytest.mark.asyncio
    async def test_multiple_tool_calls_concurrently(self) -> None:
        """Test that multiple tool calls can be made concurrently."""
        tasks = [
            handle_call_tool("mbta_get_routes", {"page_limit": 1}),
            handle_call_tool("mbta_search_stops", {"query": "Park", "limit": 1}),
            handle_call_tool("mbta_get_alerts", {"page_limit": 1}),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        assert len(results) == 3
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)

    @pytest.mark.asyncio
    async def test_pagination_parameters(self) -> None:
        """Test that pagination parameters are properly handled."""
        test_cases = [
            {"page_limit": 5},
            {"page_offset": 10},
            {"page_limit": 3, "page_offset": 5},
        ]

        for params in test_cases:
            result = await handle_call_tool("mbta_get_routes", params)
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)

    @pytest.mark.asyncio
    async def test_list_all_tools_functionality(self) -> None:
        """Test the list_all variants of tools."""
        list_all_tools = [
            "mbta_list_all_routes",
            "mbta_list_all_stops",
            "mbta_list_all_alerts",
            "mbta_list_all_facilities",
            "mbta_list_all_services",
        ]

        for tool_name in list_all_tools:
            result = await handle_call_tool(tool_name, {})
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)

    @pytest.mark.asyncio
    async def test_time_based_schedule_tool(self) -> None:
        """Test the time-based schedule query tool."""
        result = await handle_call_tool(
            "mbta_get_schedules_by_time",
            {"stop_id": "place-pktrm", "time": "08:00", "limit": 5},
        )

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

    @pytest.mark.asyncio
    async def test_amtrak_tools_integration(self) -> None:
        """Test Amtrak tools integration."""
        amtrak_tools: list[tuple[str, dict[str, int]]] = [
            ("mbta_get_amtrak_trains", {}),
            ("mbta_get_amtrak_health_status", {}),
            ("mbta_get_amtrak_trains_geojson", {}),
        ]

        for tool_name, params in amtrak_tools:
            result = await handle_call_tool(tool_name, params)
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)

    @pytest.mark.asyncio
    async def test_vehicle_position_tools(self) -> None:
        """Test vehicle position and tracking tools."""
        position_tools: list[tuple[str, dict[str, int]]] = [
            ("mbta_get_vehicle_positions", {}),
            ("mbta_get_vehicles", {"page_limit": 5}),
            ("mbta_get_track_prediction", {}),
        ]

        for tool_name, params in position_tools:
            result = await handle_call_tool(tool_name, params)
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)


class TestExtendedClientIntegration:
    """Integration tests for the ExtendedMBTAClient."""

    @pytest.mark.asyncio
    async def test_client_context_manager(self) -> None:
        """Test that client works as async context manager."""
        async with ExtendedMBTAClient() as client:
            assert client is not None
            assert hasattr(client, "get_routes")
            assert hasattr(client, "search_stops")

    @pytest.mark.asyncio
    async def test_client_with_api_key(self) -> None:
        """Test client initialization with API key."""
        test_key = "test-api-key-123"

        with patch.dict(os.environ, {"MBTA_API_KEY": test_key}):
            async with ExtendedMBTAClient() as client:
                assert client.api_key == test_key

    @pytest.mark.asyncio
    async def test_client_without_api_key(self) -> None:
        """Test client initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            async with ExtendedMBTAClient() as client:
                assert client.api_key is None


@pytest.mark.asyncio
async def test_server_startup_and_shutdown() -> None:
    """Test that server can start up and shut down cleanly."""
    # Test that we can list tools without errors
    tools = await handle_list_tools()
    assert len(tools) > 0

    # Test that we can make at least one tool call
    result = await handle_call_tool("mbta_get_routes", {"page_limit": 1})
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)


class TestTripPlanningIntegration:
    """Integration tests for trip planning functionality."""

    @pytest.mark.asyncio
    async def test_plan_trip_tool_registration(self) -> None:
        """Test that trip planning tools are properly registered."""
        tools = await handle_list_tools()
        tool_names = {tool.name for tool in tools}

        assert "mbta_plan_trip" in tool_names
        assert "mbta_get_route_alternatives" in tool_names

        # Check that the tools have proper schemas
        trip_tool = next(tool for tool in tools if tool.name == "mbta_plan_trip")
        alt_tool = next(
            tool for tool in tools if tool.name == "mbta_get_route_alternatives"
        )

        assert trip_tool.inputSchema["type"] == "object"
        assert "origin_lat" in trip_tool.inputSchema["properties"]
        assert "origin_lon" in trip_tool.inputSchema["properties"]
        assert "dest_lat" in trip_tool.inputSchema["properties"]
        assert "dest_lon" in trip_tool.inputSchema["properties"]

        assert alt_tool.inputSchema["type"] == "object"
        assert "origin_lat" in alt_tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_plan_trip_tool_execution(self) -> None:
        """Test trip planning tool execution."""
        # Test with MIT to Harvard coordinates
        result = await handle_call_tool(
            "mbta_plan_trip",
            {
                "origin_lat": 42.3601,
                "origin_lon": -71.0942,
                "dest_lat": 42.3736,
                "dest_lon": -71.1190,
                "max_walk_distance": 800,
                "max_transfers": 2,
            },
        )

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

        # Parse the JSON response
        content = json.loads(result[0].text)

        # Should have the expected structure
        assert "origin" in content
        assert "destination" in content
        assert "search_parameters" in content

        # Check coordinates are preserved
        assert content["origin"]["lat"] == 42.3601
        assert content["origin"]["lon"] == -71.0942
        assert content["destination"]["lat"] == 42.3736
        assert content["destination"]["lon"] == -71.1190

    @pytest.mark.asyncio
    async def test_plan_trip_tool_with_all_parameters(self) -> None:
        """Test trip planning tool with all optional parameters."""
        result = await handle_call_tool(
            "mbta_plan_trip",
            {
                "origin_lat": 42.3601,
                "origin_lon": -71.0942,
                "dest_lat": 42.3736,
                "dest_lon": -71.1190,
                "departure_time": "2025-01-01T10:00:00-05:00",
                "max_walk_distance": 1000,
                "max_transfers": 1,
                "prefer_fewer_transfers": False,
                "wheelchair_accessible": True,
            },
        )

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

        content = json.loads(result[0].text)
        params = content["search_parameters"]

        assert params["departure_time"] == "2025-01-01T10:00:00-05:00"
        assert params["max_walk_distance"] == 1000
        assert params["max_transfers"] == 1
        assert params["prefer_fewer_transfers"] is False
        assert params["wheelchair_accessible"] is True

    @pytest.mark.asyncio
    async def test_get_route_alternatives_tool_execution(self) -> None:
        """Test route alternatives tool execution."""
        result = await handle_call_tool(
            "mbta_get_route_alternatives",
            {
                "origin_lat": 42.3601,
                "origin_lon": -71.0942,
                "dest_lat": 42.3736,
                "dest_lon": -71.1190,
                "primary_route_modes": ["1"],  # Exclude subway
            },
        )

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

        content = json.loads(result[0].text)

        # Should have the expected structure (even if no alternatives found)
        assert "origin" in content or "error" in content

    @pytest.mark.asyncio
    async def test_plan_trip_tool_missing_required_parameters(self) -> None:
        """Test trip planning tool with missing required parameters."""
        result = await handle_call_tool(
            "mbta_plan_trip",
            {
                "origin_lat": 42.3601,
                # Missing origin_lon, dest_lat, dest_lon
            },
        )

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert "Error:" in result[0].text

    @pytest.mark.asyncio
    async def test_plan_trip_tool_invalid_coordinates(self) -> None:
        """Test trip planning tool with invalid coordinates."""
        result = await handle_call_tool(
            "mbta_plan_trip",
            {
                "origin_lat": 999.0,  # Invalid latitude
                "origin_lon": -71.0942,
                "dest_lat": 42.3736,
                "dest_lon": -71.1190,
            },
        )

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

        # Should either return error or handle gracefully
        content = result[0].text
        assert isinstance(content, str)

    @pytest.mark.asyncio
    async def test_plan_trip_tool_remote_locations(self) -> None:
        """Test trip planning tool with locations far from MBTA service area."""
        result = await handle_call_tool(
            "mbta_plan_trip",
            {
                "origin_lat": 40.7128,  # New York City
                "origin_lon": -74.0060,
                "dest_lat": 40.7589,
                "dest_lon": -73.9851,
            },
        )

        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)

        content = json.loads(result[0].text)

        # Should return error about no nearby stops
        assert "error" in content
        assert "No transit stops found" in content["error"]

    @pytest.mark.asyncio
    async def test_trip_planning_tools_with_mock_client_error(self) -> None:
        """Test trip planning tools handle client errors gracefully."""
        with patch("mbta_mcp.server.ExtendedMBTAClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.plan_trip.side_effect = Exception("Network timeout")
            mock_client_class.return_value = mock_client

            result = await handle_call_tool(
                "mbta_plan_trip",
                {
                    "origin_lat": 42.3601,
                    "origin_lon": -71.0942,
                    "dest_lat": 42.3736,
                    "dest_lon": -71.1190,
                },
            )

            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)
            assert "Error:" in result[0].text

    @pytest.mark.asyncio
    async def test_concurrent_trip_planning_calls(self) -> None:
        """Test multiple concurrent trip planning calls."""

        tasks = [
            handle_call_tool(
                "mbta_plan_trip",
                {
                    "origin_lat": 42.3601,
                    "origin_lon": -71.0942,
                    "dest_lat": 42.3736,
                    "dest_lon": -71.1190,
                },
            ),
            handle_call_tool(
                "mbta_get_route_alternatives",
                {
                    "origin_lat": 42.3601,
                    "origin_lon": -71.0942,
                    "dest_lat": 42.3736,
                    "dest_lon": -71.1190,
                },
            ),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        assert len(results) == 2
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)

    @pytest.mark.asyncio
    async def test_trip_planning_tool_schema_validation(self) -> None:
        """Test that trip planning tools have proper schema validation."""
        tools = await handle_list_tools()
        trip_tool = next(tool for tool in tools if tool.name == "mbta_plan_trip")

        # Check required fields
        required_fields = trip_tool.inputSchema.get("required", [])
        assert "origin_lat" in required_fields
        assert "origin_lon" in required_fields
        assert "dest_lat" in required_fields
        assert "dest_lon" in required_fields

        # Check optional fields have defaults
        properties = trip_tool.inputSchema["properties"]
        assert "default" in properties["max_walk_distance"]
        assert "default" in properties["max_transfers"]
        assert "default" in properties["prefer_fewer_transfers"]
        assert "default" in properties["wheelchair_accessible"]
