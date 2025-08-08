"""Test fixtures and mock data for MBTA API responses."""

from datetime import UTC, datetime
from types import TracebackType
from typing import Any

from aiohttp import ClientResponseError, RequestInfo
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL


def mock_mbta_stops_response() -> dict[str, Any]:
    """Mock MBTA stops API response."""
    return {
        "data": [
            {
                "id": "place-mit",
                "type": "stop",
                "attributes": {
                    "name": "Kendall/MIT",
                    "description": "Kendall/MIT - Red Line",
                    "latitude": 42.362491,
                    "longitude": -71.086176,
                    "zone": None,
                    "address": None,
                    "platform_code": None,
                    "platform_name": None,
                    "wheelchair_boarding": 1,
                    "location_type": 1,
                    "municipality": "Cambridge",
                },
                "relationships": {
                    "parent_station": {"data": None},
                    "child_stops": {"data": []},
                    "recommended_transfers": {"data": []},
                    "facilities": {"data": []},
                },
            },
            {
                "id": "place-hrvrd",
                "type": "stop",
                "attributes": {
                    "name": "Harvard",
                    "description": "Harvard - Red Line",
                    "latitude": 42.373362,
                    "longitude": -71.118956,
                    "zone": None,
                    "address": None,
                    "platform_code": None,
                    "platform_name": None,
                    "wheelchair_boarding": 1,
                    "location_type": 1,
                    "municipality": "Cambridge",
                },
                "relationships": {
                    "parent_station": {"data": None},
                    "child_stops": {"data": []},
                    "recommended_transfers": {"data": []},
                    "facilities": {"data": []},
                },
            },
            {
                "id": "place-pktrm",
                "type": "stop",
                "attributes": {
                    "name": "Park Street",
                    "description": "Park Street - Red Line & Green Line",
                    "latitude": 42.35639457,
                    "longitude": -71.0624242,
                    "zone": None,
                    "address": None,
                    "platform_code": None,
                    "platform_name": None,
                    "wheelchair_boarding": 1,
                    "location_type": 1,
                    "municipality": "Boston",
                },
                "relationships": {
                    "parent_station": {"data": None},
                    "child_stops": {"data": []},
                    "recommended_transfers": {"data": []},
                    "facilities": {"data": []},
                },
            },
        ],
        "jsonapi": {"version": "1.0"},
    }


def mock_mbta_predictions_response() -> dict[str, Any]:
    """Mock MBTA predictions API response."""
    base_time = datetime.now(UTC)
    return {
        "data": [
            {
                "id": "prediction-red-1",
                "type": "prediction",
                "attributes": {
                    "arrival_time": base_time.replace(minute=15).isoformat(),
                    "departure_time": base_time.replace(minute=15).isoformat(),
                    "direction_id": 0,
                    "schedule_relationship": None,
                    "status": None,
                    "stop_sequence": 10,
                },
                "relationships": {
                    "route": {"data": {"id": "Red", "type": "route"}},
                    "stop": {"data": {"id": "place-mit", "type": "stop"}},
                    "trip": {"data": {"id": "trip-red-1", "type": "trip"}},
                    "vehicle": {"data": {"id": "R-1234", "type": "vehicle"}},
                },
            },
            {
                "id": "prediction-red-2",
                "type": "prediction",
                "attributes": {
                    "arrival_time": base_time.replace(minute=22).isoformat(),
                    "departure_time": base_time.replace(minute=22).isoformat(),
                    "direction_id": 0,
                    "schedule_relationship": None,
                    "status": None,
                    "stop_sequence": 10,
                },
                "relationships": {
                    "route": {"data": {"id": "Red", "type": "route"}},
                    "stop": {"data": {"id": "place-mit", "type": "stop"}},
                    "trip": {"data": {"id": "trip-red-2", "type": "trip"}},
                    "vehicle": {"data": {"id": "R-5678", "type": "vehicle"}},
                },
            },
            {
                "id": "prediction-1-bus",
                "type": "prediction",
                "attributes": {
                    "arrival_time": base_time.replace(minute=18).isoformat(),
                    "departure_time": base_time.replace(minute=18).isoformat(),
                    "direction_id": 1,
                    "schedule_relationship": None,
                    "status": None,
                    "stop_sequence": 5,
                },
                "relationships": {
                    "route": {"data": {"id": "1", "type": "route"}},
                    "stop": {"data": {"id": "place-mit", "type": "stop"}},
                    "trip": {"data": {"id": "trip-1-bus", "type": "trip"}},
                    "vehicle": {"data": {"id": "1234", "type": "vehicle"}},
                },
            },
        ],
        "jsonapi": {"version": "1.0"},
    }


def mock_mbta_schedules_response() -> dict[str, Any]:
    """Mock MBTA schedules API response."""
    return {
        "data": [
            {
                "id": "schedule-red-1-mit",
                "type": "schedule",
                "attributes": {
                    "arrival_time": "10:15:00",
                    "departure_time": "10:15:00",
                    "drop_off_type": 0,
                    "pickup_type": 0,
                    "stop_headsign": None,
                    "stop_sequence": 10,
                    "timepoint": True,
                },
                "relationships": {
                    "route": {"data": {"id": "Red", "type": "route"}},
                    "stop": {"data": {"id": "place-mit", "type": "stop"}},
                    "trip": {"data": {"id": "trip-red-1", "type": "trip"}},
                },
            },
            {
                "id": "schedule-red-1-park",
                "type": "schedule",
                "attributes": {
                    "arrival_time": "10:18:00",
                    "departure_time": "10:18:00",
                    "drop_off_type": 0,
                    "pickup_type": 0,
                    "stop_headsign": None,
                    "stop_sequence": 12,
                    "timepoint": True,
                },
                "relationships": {
                    "route": {"data": {"id": "Red", "type": "route"}},
                    "stop": {"data": {"id": "place-pktrm", "type": "stop"}},
                    "trip": {"data": {"id": "trip-red-1", "type": "trip"}},
                },
            },
            {
                "id": "schedule-red-1-harvard",
                "type": "schedule",
                "attributes": {
                    "arrival_time": "10:25:00",
                    "departure_time": "10:25:00",
                    "drop_off_type": 0,
                    "pickup_type": 0,
                    "stop_headsign": None,
                    "stop_sequence": 20,
                    "timepoint": True,
                },
                "relationships": {
                    "route": {"data": {"id": "Red", "type": "route"}},
                    "stop": {"data": {"id": "place-hrvrd", "type": "stop"}},
                    "trip": {"data": {"id": "trip-red-1", "type": "trip"}},
                },
            },
        ],
        "jsonapi": {"version": "1.0"},
    }


def mock_mbta_routes_response() -> dict[str, Any]:
    """Mock MBTA routes API response."""
    return {
        "data": [
            {
                "id": "Red",
                "type": "route",
                "attributes": {
                    "color": "DA291C",
                    "description": "Rapid Transit",
                    "direction_destinations": ["Ashmont/Braintree", "Alewife"],
                    "direction_names": ["South", "North"],
                    "fare_class": "Rapid Transit",
                    "long_name": "Red Line",
                    "short_name": "",
                    "sort_order": 10010,
                    "text_color": "FFFFFF",
                    "type": 1,
                },
                "relationships": {
                    "line": {"data": {"id": "line-Red", "type": "line"}},
                    "route_patterns": {"data": []},
                },
            },
            {
                "id": "1",
                "type": "route",
                "attributes": {
                    "color": "FFC72C",
                    "description": "Key Bus Route",
                    "direction_destinations": ["Harvard Square", "Nubian Station"],
                    "direction_names": ["Outbound", "Inbound"],
                    "fare_class": "Local Bus",
                    "long_name": "Harvard Square - Nubian Station",
                    "short_name": "1",
                    "sort_order": 10010,
                    "text_color": "000000",
                    "type": 3,
                },
                "relationships": {
                    "line": {"data": None},
                    "route_patterns": {"data": []},
                },
            },
        ],
        "jsonapi": {"version": "1.0"},
    }


def mock_mbta_trips_response() -> dict[str, Any]:
    """Mock MBTA trips API response."""
    return {
        "data": [
            {
                "id": "trip-red-1",
                "type": "trip",
                "attributes": {
                    "block_id": "B123",
                    "direction_id": 0,
                    "headsign": "Braintree",
                    "name": "",
                    "wheelchair_accessible": 1,
                },
                "relationships": {
                    "route": {"data": {"id": "Red", "type": "route"}},
                    "route_pattern": {
                        "data": {"id": "Red-1-0", "type": "route_pattern"}
                    },
                    "service": {
                        "data": {"id": "BUS12024-hbs24024-Wdy01", "type": "service"}
                    },
                    "shape": {"data": {"id": "9840004", "type": "shape"}},
                },
            },
        ],
        "jsonapi": {"version": "1.0"},
    }


def mock_empty_mbta_response() -> dict[str, Any]:
    """Mock empty MBTA API response."""
    return {
        "data": [],
        "jsonapi": {"version": "1.0"},
    }


def mock_mbta_error_response(
    status_code: int = 429, message: str = "Too Many Requests"
) -> dict[str, Any]:
    """Mock MBTA API error response."""
    return {
        "errors": [
            {
                "status": str(status_code),
                "title": message,
                "detail": f"API Error: {message}",
            }
        ],
        "jsonapi": {"version": "1.0"},
    }


class MockMBTAResponse:
    """Mock aiohttp response for MBTA API."""

    def __init__(self, data: dict[str, Any], status: int = 200):
        self.data = data
        self.status = status

    async def json(self) -> dict[str, Any]:
        """Return JSON data."""
        return self.data

    def raise_for_status(self) -> None:
        """Raise exception for non-200 status codes."""
        http_error_threshold = 400
        if self.status >= http_error_threshold:
            # Create minimal RequestInfo for testing
            headers = CIMultiDict[str]()
            headers_proxy = CIMultiDictProxy(headers)
            request_info = RequestInfo(
                url=URL("http://test.com"),
                method="GET",
                headers=headers_proxy,
                real_url=URL("http://test.com"),
            )

            raise ClientResponseError(
                request_info=request_info,
                history=(),
                status=self.status,
                message=f"HTTP {self.status}",
            )

    async def __aenter__(self) -> "MockMBTAResponse":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        return


def get_mock_response_for_url(
    url: str, params: dict[str, Any] | None = None
) -> MockMBTAResponse:
    """Get appropriate mock response based on URL and parameters."""
    # Constants for NYC coordinates (remote from Boston area)
    nyc_lat = 40.7128
    nyc_lon = -74.0060
    coordinate_tolerance = 0.5

    # Handle stops endpoint with special NYC logic
    if "/stops" in url:
        # Check for empty result scenarios (e.g., remote locations like NYC)
        if params:
            lat = params.get("filter[latitude]")
            lon = params.get("filter[longitude]")
            # NYC area coordinates should return empty results
            if (
                lat
                and lon
                and (
                    abs(float(lat) - nyc_lat) < coordinate_tolerance
                    and abs(float(lon) - nyc_lon) < coordinate_tolerance
                )
            ):
                return MockMBTAResponse(mock_empty_mbta_response())

        # Return stops response for Boston area
        return MockMBTAResponse(mock_mbta_stops_response())

    # Map URL patterns to response functions
    url_response_map = {
        "/predictions": mock_mbta_predictions_response,
        "/schedules": mock_mbta_schedules_response,
        "/routes": mock_mbta_routes_response,
        "/trips": mock_mbta_trips_response,
    }

    # Find matching URL pattern and return corresponding response
    for pattern, response_func in url_response_map.items():
        if pattern in url:
            return MockMBTAResponse(response_func())

    # Default empty response for unknown endpoints
    return MockMBTAResponse(mock_empty_mbta_response())
