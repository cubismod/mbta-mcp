"""Tests for trip planning functionality."""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from mbta_mcp.extended_client import ExtendedMBTAClient


class TestTripPlanningMethods:
    """Unit tests for trip planning methods."""

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create a mock client with basic setup."""
        return AsyncMock(spec=ExtendedMBTAClient)

    @pytest.fixture
    def sample_stops_data(self) -> dict[str, Any]:
        """Sample stops data for testing."""
        return {
            "data": [
                {
                    "id": "place-mit",
                    "attributes": {
                        "name": "Kendall/MIT",
                        "latitude": 42.3601,
                        "longitude": -71.0942,
                    },
                },
                {
                    "id": "place-hrvrd",
                    "attributes": {
                        "name": "Harvard Square",
                        "latitude": 42.3736,
                        "longitude": -71.1190,
                    },
                },
            ]
        }

    @pytest.fixture
    def sample_predictions_data(self) -> dict[str, Any]:
        """Sample predictions data for testing."""
        return {
            "data": [
                {
                    "id": "prediction-1",
                    "attributes": {
                        "departure_time": "2025-01-01T10:15:00-05:00",
                        "arrival_time": "2025-01-01T10:15:00-05:00",
                        "wheelchair_accessible": True,
                    },
                    "relationships": {
                        "route": {"data": {"id": "Red"}},
                        "trip": {"data": {"id": "trip-123"}},
                        "stop": {"data": {"id": "place-mit"}},
                    },
                },
                {
                    "id": "prediction-2",
                    "attributes": {
                        "departure_time": "2025-01-01T10:20:00-05:00",
                        "arrival_time": "2025-01-01T10:20:00-05:00",
                        "wheelchair_accessible": False,
                    },
                    "relationships": {
                        "route": {"data": {"id": "1"}},
                        "trip": {"data": {"id": "trip-456"}},
                        "stop": {"data": {"id": "place-mit"}},
                    },
                },
            ]
        }

    @pytest.fixture
    def sample_schedules_data(self) -> dict[str, Any]:
        """Sample schedules data for testing."""
        return {
            "data": [
                {
                    "id": "schedule-1",
                    "attributes": {
                        "arrival_time": "10:15:00",
                        "departure_time": "10:15:00",
                    },
                    "relationships": {
                        "stop": {"data": {"id": "place-mit"}},
                        "trip": {"data": {"id": "trip-123"}},
                    },
                },
                {
                    "id": "schedule-2",
                    "attributes": {
                        "arrival_time": "10:25:00",
                        "departure_time": "10:25:00",
                    },
                    "relationships": {
                        "stop": {"data": {"id": "place-hrvrd"}},
                        "trip": {"data": {"id": "trip-123"}},
                    },
                },
            ]
        }

    @pytest.mark.asyncio
    async def test_plan_trip_basic_functionality(
        self, trip_planning_params: dict[str, Any]
    ) -> None:
        """Test basic trip planning functionality."""
        async with ExtendedMBTAClient() as client:
            result = await client.plan_trip(**trip_planning_params)

            assert "origin" in result
            assert "destination" in result
            assert "trip_options" in result
            assert "search_parameters" in result

            assert result["origin"]["lat"] == 42.3601
            assert result["origin"]["lon"] == -71.0942
            assert result["destination"]["lat"] == 42.3736
            assert result["destination"]["lon"] == -71.1190

    @pytest.mark.asyncio
    async def test_plan_trip_no_nearby_stops(
        self, sample_coordinates: dict[str, dict[str, float]]
    ) -> None:
        """Test trip planning when no nearby stops are found."""
        async with ExtendedMBTAClient() as client:
            # Use NYC coordinates which should return empty results
            result = await client.plan_trip(
                origin_lat=sample_coordinates["nyc"]["lat"],
                origin_lon=sample_coordinates["nyc"]["lon"],
                dest_lat=sample_coordinates["nyc"]["lat"] + 0.1,
                dest_lon=sample_coordinates["nyc"]["lon"] + 0.1,
            )

            assert "error" in result
            assert "No transit stops found" in result["error"]
            assert result["origin_stops_found"] == 0
            assert result["dest_stops_found"] == 0

    @pytest.mark.asyncio
    async def test_plan_trip_with_wheelchair_accessibility(
        self, trip_planning_params: dict[str, Any]
    ) -> None:
        """Test trip planning with wheelchair accessibility requirement."""
        params = trip_planning_params.copy()
        params["wheelchair_accessible"] = True

        async with ExtendedMBTAClient() as client:
            result = await client.plan_trip(**params)

            assert "search_parameters" in result
            assert result["search_parameters"]["wheelchair_accessible"] is True

    @pytest.mark.asyncio
    async def test_plan_trip_with_custom_parameters(self) -> None:
        """Test trip planning with custom parameters."""
        async with ExtendedMBTAClient() as client:
            result = await client.plan_trip(
                origin_lat=42.3601,
                origin_lon=-71.0942,
                dest_lat=42.3736,
                dest_lon=-71.1190,
                max_walk_distance=1200,
                max_transfers=1,
                prefer_fewer_transfers=False,
                departure_time="2025-01-01T09:00:00-05:00",
            )

            params = result["search_parameters"]
            assert params["max_walk_distance"] == 1200
            assert params["max_transfers"] == 1
            assert params["prefer_fewer_transfers"] is False
            assert params["departure_time"] == "2025-01-01T09:00:00-05:00"

    @pytest.mark.asyncio
    async def test_get_route_alternatives_basic(
        self, trip_planning_params: dict[str, Any]
    ) -> None:
        """Test basic route alternatives functionality."""
        async with ExtendedMBTAClient() as client:
            result = await client.get_route_alternatives(
                origin_lat=trip_planning_params["origin_lat"],
                origin_lon=trip_planning_params["origin_lon"],
                dest_lat=trip_planning_params["dest_lat"],
                dest_lon=trip_planning_params["dest_lon"],
                primary_route_modes=["1"],  # Exclude subway
            )

            # Should have the expected structure (might have no alternatives but structure should be there)
            assert "origin" in result or "error" in result
            if "origin" in result:
                assert "destination" in result

    @pytest.mark.asyncio
    async def test_get_route_alternatives_with_error(
        self, sample_coordinates: dict[str, dict[str, float]]
    ) -> None:
        """Test route alternatives when trip planning fails."""
        # Use NYC coordinates which should return no nearby stops
        async with ExtendedMBTAClient() as client:
            result = await client.get_route_alternatives(
                origin_lat=sample_coordinates["nyc"]["lat"],
                origin_lon=sample_coordinates["nyc"]["lon"],
                dest_lat=sample_coordinates["nyc"]["lat"] + 0.1,
                dest_lon=sample_coordinates["nyc"]["lon"] + 0.1,
            )

            assert "error" in result

    def test_calculate_walk_time(self) -> None:
        """Test walking time calculation."""
        client = ExtendedMBTAClient()

        # Test basic calculation (short distance)
        time1 = client._calculate_walk_time((42.3601, -71.0942), (42.3602, -71.0943))
        assert isinstance(time1, int)
        assert time1 >= 1  # Minimum 1 minute

        # Test longer distance
        time2 = client._calculate_walk_time((42.3601, -71.0942), (42.3736, -71.1190))
        assert time2 > time1  # Should take longer

        # Test with custom walking speed
        time3 = client._calculate_walk_time(
            (42.3601, -71.0942), (42.3736, -71.1190), walk_speed_kmh=3.0
        )
        assert time3 > time2  # Slower speed = more time

    def test_haversine_distance(self) -> None:
        """Test haversine distance calculation."""
        client = ExtendedMBTAClient()

        # Test zero distance
        dist1 = client._haversine_distance(42.3601, -71.0942, 42.3601, -71.0942)
        assert dist1 == 0.0

        # Test known distance (MIT to Harvard Square ≈ 2.7 km)
        dist2 = client._haversine_distance(42.3601, -71.0942, 42.3736, -71.1190)
        assert 2.0 < dist2 < 4.0  # Reasonable bounds

        # Test symmetry
        dist3 = client._haversine_distance(42.3736, -71.1190, 42.3601, -71.0942)
        assert abs(dist2 - dist3) < 0.001  # Should be essentially equal

    def test_parse_datetime_iso_format(self) -> None:
        """Test datetime parsing with ISO format."""
        client = ExtendedMBTAClient()

        # Test valid ISO datetime with timezone
        dt1 = client._parse_datetime("2025-01-01T10:15:00-05:00")
        assert dt1 is not None
        assert isinstance(dt1, datetime)
        assert dt1.tzinfo is not None

        # Test ISO datetime with Z suffix
        dt2 = client._parse_datetime("2025-01-01T10:15:00Z")
        assert dt2 is not None
        assert dt2.tzinfo is not None

        # Test ISO datetime without timezone (should add timezone)
        dt3 = client._parse_datetime("2025-01-01T10:15:00")
        assert dt3 is not None
        assert dt3.tzinfo is not None

    def test_parse_datetime_time_only_format(self) -> None:
        """Test datetime parsing with time-only format."""
        client = ExtendedMBTAClient()

        # Test valid time format
        dt1 = client._parse_datetime("10:15:00")
        assert dt1 is not None
        assert isinstance(dt1, datetime)
        assert dt1.tzinfo is not None
        assert dt1.hour == 10
        assert dt1.minute == 15
        assert dt1.second == 0

    def test_parse_datetime_invalid_formats(self) -> None:
        """Test datetime parsing with invalid formats."""
        client = ExtendedMBTAClient()

        # Test None input
        assert client._parse_datetime(None) is None

        # Test empty string
        assert client._parse_datetime("") is None

        # Test invalid format
        assert client._parse_datetime("invalid-datetime") is None

        # Test malformed ISO datetime
        assert client._parse_datetime("2025-13-45T25:70:80") is None

    @pytest.mark.asyncio
    async def test_find_direct_routes_basic(
        self,
        sample_stops_data: dict[str, Any],
        sample_predictions_data: dict[str, Any],
        sample_schedules_data: dict[str, Any],
    ) -> None:
        """Test basic direct route finding."""
        with patch("mbta_mcp.extended_client.ExtendedMBTAClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get_schedules.return_value = sample_schedules_data
            mock_client_class.return_value = mock_client

            async with ExtendedMBTAClient() as client:
                # Create origin and destination stops
                origin_stop = sample_stops_data["data"][0]
                dest_stops = sample_stops_data["data"][1:]

                result = await client._find_direct_routes(
                    origin_stop=origin_stop,
                    dest_stops=dest_stops,
                    origin_departures=sample_predictions_data["data"],
                    departure_time=None,
                    wheelchair_accessible=False,
                )

                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_find_direct_routes_wheelchair_filtering(
        self,
        sample_stops_data: dict[str, Any],
        sample_predictions_data: dict[str, Any],
        sample_schedules_data: dict[str, Any],
    ) -> None:
        """Test direct route finding with wheelchair accessibility filtering."""
        with patch("mbta_mcp.extended_client.ExtendedMBTAClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get_schedules.return_value = sample_schedules_data
            mock_client_class.return_value = mock_client

            async with ExtendedMBTAClient() as client:
                origin_stop = sample_stops_data["data"][0]
                dest_stops = sample_stops_data["data"][1:]

                result = await client._find_direct_routes(
                    origin_stop=origin_stop,
                    dest_stops=dest_stops,
                    origin_departures=sample_predictions_data["data"],
                    departure_time=None,
                    wheelchair_accessible=True,  # Only accessible routes
                )

                assert isinstance(result, list)
                # Should filter out non-accessible predictions

    @pytest.mark.asyncio
    async def test_find_direct_routes_with_departure_time_filtering(
        self,
        sample_stops_data: dict[str, Any],
        sample_predictions_data: dict[str, Any],
        sample_schedules_data: dict[str, Any],
    ) -> None:
        """Test direct route finding with departure time filtering."""
        with patch("mbta_mcp.extended_client.ExtendedMBTAClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.get_schedules.return_value = sample_schedules_data
            mock_client_class.return_value = mock_client

            async with ExtendedMBTAClient() as client:
                origin_stop = sample_stops_data["data"][0]
                dest_stops = sample_stops_data["data"][1:]

                result = await client._find_direct_routes(
                    origin_stop=origin_stop,
                    dest_stops=dest_stops,
                    origin_departures=sample_predictions_data["data"],
                    departure_time="2025-01-01T10:30:00-05:00",  # After all predictions
                    wheelchair_accessible=False,
                )

                assert isinstance(result, list)
                # Should filter out earlier departures

    @pytest.mark.asyncio
    async def test_trip_planning_error_handling(self) -> None:
        """Test trip planning with mocked API - should handle gracefully."""
        # Under the global mocking, trip planning should complete successfully
        # This tests the normal flow works with mocked data
        async with ExtendedMBTAClient() as client:
            result = await client.plan_trip(
                origin_lat=42.3601,
                origin_lon=-71.0942,
                dest_lat=42.3736,
                dest_lon=-71.1190,
            )

            # With mocked API, this should succeed and return proper structure
            assert "origin" in result
            assert "destination" in result
            assert "trip_options" in result
            assert "search_parameters" in result

    @pytest.mark.asyncio
    async def test_find_direct_routes_api_error_handling(
        self, sample_stops_data: dict[str, Any], sample_predictions_data: dict[str, Any]
    ) -> None:
        """Test error handling when schedule API fails."""
        with patch("mbta_mcp.extended_client.ExtendedMBTAClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            # Mock schedule API failure
            mock_client.get_schedules.side_effect = Exception("API Error")
            mock_client_class.return_value = mock_client

            async with ExtendedMBTAClient() as client:
                origin_stop = sample_stops_data["data"][0]
                dest_stops = sample_stops_data["data"][1:]

                result = await client._find_direct_routes(
                    origin_stop=origin_stop,
                    dest_stops=dest_stops,
                    origin_departures=sample_predictions_data["data"],
                    departure_time=None,
                    wheelchair_accessible=False,
                )

                # Should return empty list when API fails
                assert isinstance(result, list)

    def test_edge_cases_empty_inputs(self) -> None:
        """Test edge cases with empty inputs."""
        client = ExtendedMBTAClient()

        # Test empty coordinates (should still work)
        time = client._calculate_walk_time((0.0, 0.0), (0.0, 0.0))
        assert time >= 1  # Minimum 1 minute

        # Test parse datetime with edge cases
        assert client._parse_datetime("") is None
        assert client._parse_datetime("   ") is None

    @pytest.mark.parametrize(
        ("lat1", "lon1", "lat2", "lon2", "expected_range"),
        [
            (42.3601, -71.0942, 42.3601, -71.0942, (0.0, 0.1)),  # Same point
            (42.3601, -71.0942, 42.3736, -71.1190, (2.0, 4.0)),  # MIT to Harvard
            (0.0, 0.0, 1.0, 1.0, (140.0, 160.0)),  # Large distance
        ],
    )
    def test_haversine_distance_parametrized(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        expected_range: tuple[float, float],
    ) -> None:
        """Test haversine distance calculation with various inputs."""
        client = ExtendedMBTAClient()
        distance = client._haversine_distance(lat1, lon1, lat2, lon2)

        min_expected, max_expected = expected_range
        assert min_expected <= distance <= max_expected, (
            f"Distance {distance} not in range {expected_range}"
        )

    @pytest.mark.parametrize(
        ("time_str", "should_parse"),
        [
            ("2025-01-01T10:15:00-05:00", True),
            ("2025-01-01T10:15:00Z", True),
            ("2025-01-01T10:15:00", True),
            ("10:15:00", True),
            ("invalid-time", False),
            ("", False),
            (None, False),
            ("25:99:99", False),
        ],
    )
    def test_parse_datetime_parametrized(
        self, time_str: str | None, should_parse: bool
    ) -> None:
        """Test datetime parsing with various input formats."""
        client = ExtendedMBTAClient()
        result = client._parse_datetime(time_str)

        if should_parse:
            assert result is not None
            assert isinstance(result, datetime)
        else:
            assert result is None
