"""Extended MBTA V3 API client with comprehensive endpoint coverage."""

import logging
from typing import Any

from async_lru import alru_cache

from .client import MBTAClient
from .fuzzy_filter import filter_data_fuzzy

logger = logging.getLogger(__name__)

PAGE_LIMIT = 175


class ExtendedMBTAClient(MBTAClient):
    """Extended client with all MBTA V3 API endpoints."""

    async def __aenter__(self) -> "ExtendedMBTAClient":
        await super().__aenter__()
        return self

    @alru_cache(maxsize=100, ttl=10)
    async def get_vehicle_positions(self) -> dict[str, Any]:
        """Get real-time vehicle positions from the external API.

        Fetches vehicle position data from https://vehicles.ryanwallace.cloud/
        which provides GeoJSON format data with vehicle locations, routes, and status.
        """
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        url = "https://vehicles.ryanwallace.cloud/"

        async with self.session.get(url) as response:
            response.raise_for_status()
            result: dict[str, Any] = await response.json()

            return result

    async def get_external_alerts(self) -> dict[str, Any]:
        """Get general alerts from the external API.

        Fetches alert data from https://vehicles.ryanwallace.cloud/alerts
        which provides real-time service alerts, delays, and disruptions.
        """
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        url = "https://vehicles.ryanwallace.cloud/alerts"

        async with self.session.get(url) as response:
            response.raise_for_status()
            result: dict[str, Any] = await response.json()

            return result

    @alru_cache(maxsize=100, ttl=10)
    async def get_track_prediction(
        self,
        station_id: str,
        route_id: str,
        trip_id: str,
        headsign: str,
        direction_id: int,
        scheduled_time: str,
    ) -> dict[str, Any]:
        """Get track prediction for a specific trip.

        Uses the IMT Track Prediction API to predict which track a train will use.
        """
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        url = "https://imt.ryanwallace.cloud/predictions"
        params = {
            "station_id": station_id,
            "route_id": route_id,
            "trip_id": trip_id,
            "headsign": headsign,
            "direction_id": str(direction_id),
            "scheduled_time": scheduled_time,
        }

        async with self.session.post(url, params=params) as response:
            response.raise_for_status()
            result: dict[str, Any] = await response.json()

            return result

    async def get_chained_track_predictions(
        self, predictions: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Get multiple track predictions in a single request.

        Uses the IMT Track Prediction API for batch predictions.
        """
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        url = "https://imt.ryanwallace.cloud/chained-predictions"
        data = {"predictions": predictions}

        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            result: dict[str, Any] = await response.json()
            return result

    @alru_cache(maxsize=100, ttl=10)
    async def get_prediction_stats(
        self, station_id: str, route_id: str
    ) -> dict[str, Any]:
        """Get prediction statistics for a station and route.

        Returns accuracy metrics and performance data for track predictions.
        """
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        url = f"https://imt.ryanwallace.cloud/stats/{station_id}/{route_id}"

        async with self.session.get(url) as response:
            response.raise_for_status()
            result: dict[str, Any] = await response.json()
            return result

    @alru_cache(maxsize=100, ttl=10)
    async def get_historical_assignments(
        self, station_id: str, route_id: str, days: int = 30
    ) -> dict[str, Any]:
        """Get historical track assignments for analysis.

        Returns historical data showing actual track assignments for analysis.
        """
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        url = f"https://imt.ryanwallace.cloud/historical/{station_id}/{route_id}"
        params = {"days": days}

        async with self.session.get(url, params=params) as response:
            response.raise_for_status()
            result: dict[str, Any] = await response.json()
            return result

    @alru_cache(maxsize=100, ttl=10)
    async def get_amtrak_trains(self) -> list[dict[str, Any]]:
        """Get all tracked Amtrak trains from the Boston Amtrak Tracker API.

        Fetches real-time Amtrak train data from https://bos.ryanwallace.cloud/
        which provides train locations, routes, status, and other information.
        """
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        url = "https://bos.ryanwallace.cloud/trains"

        async with self.session.get(url) as response:
            response.raise_for_status()
            result: list[dict[str, Any]] = await response.json()

            return result

    @alru_cache(maxsize=100, ttl=10)
    async def get_amtrak_trains_geojson(self) -> dict[str, Any]:
        """Get Amtrak trains as GeoJSON for mapping applications.

        Fetches Amtrak train data formatted as GeoJSON from https://bos.ryanwallace.cloud/
        which provides train locations in a format suitable for mapping.
        """
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        url = "https://bos.ryanwallace.cloud/trains/geojson"

        async with self.session.get(url) as response:
            response.raise_for_status()
            result: dict[str, Any] = await response.json()
            return result

    @alru_cache(maxsize=100, ttl=10)
    async def get_amtrak_health_status(self) -> dict[str, Any]:
        """Get health status of the Boston Amtrak Tracker API.

        Returns server health status and last data update time.
        """
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        url = "https://bos.ryanwallace.cloud/health"

        async with self.session.get(url) as response:
            response.raise_for_status()
            result: dict[str, Any] = await response.json()
            return result

    async def get_services(
        self, service_id: str | None = None, page_limit: int = 10
    ) -> dict[str, Any]:
        """Get service definitions."""
        endpoint = f"/services/{service_id}" if service_id else "/services"
        params: dict[str, Any] = {"page[limit]": page_limit}
        return await self._request(endpoint, params)

    async def get_shapes(
        self,
        shape_id: str | None = None,
        route_id: str | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get route shapes/paths."""
        endpoint = f"/shapes/{shape_id}" if shape_id else "/shapes"
        params: dict[str, Any] = {"page[limit]": page_limit}
        if route_id:
            params["filter[route]"] = route_id
        return await self._request(endpoint, params)

    async def get_facilities(
        self,
        facility_id: str | None = None,
        stop_id: str | None = None,
        facility_type: str | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get facility information (elevators, escalators, etc.)."""
        endpoint = f"/facilities/{facility_id}" if facility_id else "/facilities"
        params: dict[str, Any] = {"page[limit]": page_limit}
        if stop_id:
            params["filter[stop]"] = stop_id
        if facility_type:
            params["filter[type]"] = facility_type
        return await self._request(endpoint, params)

    async def get_live_facilities(
        self, facility_id: str | None = None, page_limit: int = 10
    ) -> dict[str, Any]:
        """Get live facility status."""
        endpoint = (
            f"/live_facilities/{facility_id}" if facility_id else "/live_facilities"
        )
        params: dict[str, Any] = {"page[limit]": page_limit}
        return await self._request(endpoint, params)

    async def get_lines(
        self, line_id: str | None = None, page_limit: int = 10
    ) -> dict[str, Any]:
        """Get line information."""
        endpoint = f"/lines/{line_id}" if line_id else "/lines"
        params: dict[str, Any] = {"page[limit]": page_limit}
        return await self._request(endpoint, params)

    async def get_route_patterns(
        self,
        route_pattern_id: str | None = None,
        route_id: str | None = None,
        direction_id: int | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get route patterns."""
        endpoint = (
            f"/route_patterns/{route_pattern_id}"
            if route_pattern_id
            else "/route_patterns"
        )
        params: dict[str, Any] = {"page[limit]": page_limit}
        if route_id:
            params["filter[route]"] = route_id
        if direction_id is not None:
            params["filter[direction_id]"] = direction_id
        return await self._request(endpoint, params)

    async def search_stops(
        self,
        query: str,
        latitude: float | None = None,
        longitude: float | None = None,
        radius: float | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Search for stops by name or location using fuzzy matching.

        Note: MBTA API doesn't support text search filters.
        This method fetches stops and filters by name client-side using fuzzy matching.
        For better performance, also provide latitude/longitude.
        """
        # Fetch more to filter client-side
        params: dict[str, Any] = {"page[limit]": min(page_limit * 10, PAGE_LIMIT)}

        # If location provided, use it to narrow results
        if latitude is not None and longitude is not None:
            params["filter[latitude]"] = latitude
            params["filter[longitude]"] = longitude
            if radius is not None:
                params["filter[radius]"] = radius

        # Get stops from API
        result = await self._request("/stops", params)

        # Filter by name client-side using fuzzy matching
        if "data" in result and query:
            search_fields = ["attributes.name", "attributes.description", "id"]
            filtered_data = filter_data_fuzzy(
                result["data"], query, search_fields, page_limit
            )
            result["data"] = filtered_data

        return result

    async def get_nearby_stops(
        self,
        latitude: float,
        longitude: float,
        radius: float = 1000,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get stops near a specific location."""
        params: dict[str, Any] = {
            "page[limit]": page_limit,
            "filter[latitude]": latitude,
            "filter[longitude]": longitude,
            "filter[radius]": radius,
        }
        return await self._request("/stops", params)

    async def get_predictions_for_stop(
        self,
        stop_id: str,
        route_id: str | None = None,
        direction_id: int | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get all predictions for a specific stop."""
        params: dict[str, Any] = {"page[limit]": page_limit, "filter[stop]": stop_id}
        if route_id:
            params["filter[route]"] = route_id
        if direction_id is not None:
            params["filter[direction_id]"] = direction_id
        return await self._request("/predictions", params)

    async def get_schedule_for_stop(
        self,
        stop_id: str,
        route_id: str | None = None,
        direction_id: int | None = None,
        min_time: str | None = None,
        max_time: str | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get schedule for a specific stop with time filtering."""
        params: dict[str, Any] = {"page[limit]": page_limit, "filter[stop]": stop_id}
        if route_id:
            params["filter[route]"] = route_id
        if direction_id is not None:
            params["filter[direction_id]"] = direction_id
        if min_time:
            params["filter[min_time]"] = min_time
        if max_time:
            params["filter[max_time]"] = max_time
        return await self._request("/schedules", params)

    async def get_alerts_for_stop(
        self, stop_id: str, severity: int | None = None, page_limit: int = 10
    ) -> dict[str, Any]:
        """Get alerts affecting a specific stop."""
        params: dict[str, Any] = {"page[limit]": page_limit, "filter[stop]": stop_id}
        if severity is not None:
            params["filter[severity]"] = severity
        return await self._request("/alerts", params)

    async def get_alerts_for_route(
        self, route_id: str, severity: int | None = None, page_limit: int = 10
    ) -> dict[str, Any]:
        """Get alerts affecting a specific route."""
        params: dict[str, Any] = {"page[limit]": page_limit, "filter[route]": route_id}
        if severity is not None:
            params["filter[severity]"] = severity
        return await self._request("/alerts", params)

    async def get_vehicles_for_route(
        self, route_id: str, direction_id: int | None = None, page_limit: int = 10
    ) -> dict[str, Any]:
        """Get all vehicles for a specific route."""
        params: dict[str, Any] = {"page[limit]": page_limit, "filter[route]": route_id}
        if direction_id is not None:
            params["filter[direction_id]"] = direction_id
        return await self._request("/vehicles", params)

    async def get_trip_details(
        self,
        trip_id: str,
        include_predictions: bool = False,
        include_schedule: bool = False,
        include_vehicle: bool = False,
    ) -> dict[str, Any]:
        """Get detailed trip information with optional includes."""
        params: dict[str, Any] = {}
        includes = []
        if include_predictions:
            includes.append("predictions")
        if include_schedule:
            includes.append("schedule")
        if include_vehicle:
            includes.append("vehicle")
        if includes:
            params["include"] = ",".join(includes)
        return await self._request(f"/trips/{trip_id}", params)

    async def get_route_with_stops(
        self, route_id: str, direction_id: int | None = None
    ) -> dict[str, Any]:
        """Get route information including all stops."""
        params: dict[str, Any] = {"include": "stops"}
        if direction_id is not None:
            params["filter[direction_id]"] = direction_id
        return await self._request(f"/routes/{route_id}", params)

    async def list_all_alerts(
        self, query: str | None = None, max_results: int = 50
    ) -> dict[str, Any]:
        """List all alerts with optional fuzzy filtering."""
        # Fetch maximum number of alerts to filter client-side
        result = await self._request("/alerts", {"page[limit]": PAGE_LIMIT})

        if query and "data" in result:
            search_fields = ["attributes.header", "attributes.description", "id"]
            filtered_data = filter_data_fuzzy(
                result["data"], query, search_fields, max_results
            )
            result["data"] = filtered_data
        elif "data" in result:
            result["data"] = result["data"][:max_results]

        return result

    async def list_all_facilities(
        self, query: str | None = None, max_results: int = 50
    ) -> dict[str, Any]:
        """List all facilities with optional fuzzy filtering."""
        # Fetch maximum number of facilities to filter client-side
        result = await self._request("/facilities", {"page[limit]": PAGE_LIMIT})

        if query and "data" in result:
            search_fields = ["attributes.short_name", "attributes.long_name", "id"]
            filtered_data = filter_data_fuzzy(
                result["data"], query, search_fields, max_results
            )
            result["data"] = filtered_data
        elif "data" in result:
            result["data"] = result["data"][:max_results]

        return result

    async def list_all_lines(
        self, query: str | None = None, max_results: int = 50
    ) -> dict[str, Any]:
        """List all lines with optional fuzzy filtering."""
        # Fetch maximum number of lines to filter client-side
        result = await self._request("/lines", {"page[limit]": PAGE_LIMIT})

        if query and "data" in result:
            search_fields = ["attributes.short_name", "attributes.long_name", "id"]
            filtered_data = filter_data_fuzzy(
                result["data"], query, search_fields, max_results
            )
            result["data"] = filtered_data
        elif "data" in result:
            result["data"] = result["data"][:max_results]

        return result

    async def list_all_routes(
        self, query: str | None = None, max_results: int = 50
    ) -> dict[str, Any]:
        """List all routes with optional fuzzy filtering."""
        # Fetch maximum number of routes to filter client-side
        result = await self._request("/routes", {"page[limit]": PAGE_LIMIT})

        if query and "data" in result:
            search_fields = ["attributes.short_name", "attributes.long_name", "id"]
            filtered_data = filter_data_fuzzy(
                result["data"], query, search_fields, max_results
            )
            result["data"] = filtered_data
        elif "data" in result:
            result["data"] = result["data"][:max_results]

        return result

    async def list_all_services(
        self, query: str | None = None, max_results: int = 50
    ) -> dict[str, Any]:
        """List all services with optional fuzzy filtering."""
        # Fetch maximum number of services to filter client-side
        result = await self._request("/services", {"page[limit]": PAGE_LIMIT})

        if query and "data" in result:
            search_fields = ["attributes.description", "id"]
            filtered_data = filter_data_fuzzy(
                result["data"], query, search_fields, max_results
            )
            result["data"] = filtered_data
        elif "data" in result:
            result["data"] = result["data"][:max_results]

        return result

    async def list_all_stops(
        self, query: str | None = None, max_results: int = 50
    ) -> dict[str, Any]:
        """List all stops with optional fuzzy filtering."""
        # Fetch maximum number of stops to filter client-side
        result = await self._request("/stops", {"page[limit]": PAGE_LIMIT})

        if query and "data" in result:
            search_fields = ["attributes.name", "attributes.description", "id"]
            filtered_data = filter_data_fuzzy(
                result["data"], query, search_fields, max_results
            )
            result["data"] = filtered_data
        elif "data" in result:
            result["data"] = result["data"][:max_results]

        return result

    async def get_schedules_by_time(
        self,
        date: str | None = None,
        min_time: str | None = None,
        max_time: str | None = None,
        route_id: str | None = None,
        stop_id: str | None = None,
        trip_id: str | None = None,
        direction_id: int | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get schedules filtered by specific times and dates.

        Args:
            date: Filter by service date (YYYY-MM-DD format).
            min_time: Filter schedules at or after this time (HH:MM format).
                     Use >24:00 for times after midnight (e.g., 25:30).
            max_time: Filter schedules at or before this time (HH:MM format).
            route_id: Filter by specific route.
            stop_id: Filter by specific stop.
            trip_id: Filter by specific trip.
            direction_id: Filter by direction (0 or 1).
            page_limit: Maximum number of results to return.
        """
        params: dict[str, Any] = {"page[limit]": page_limit}

        if date:
            params["filter[date]"] = date
        if min_time:
            params["filter[min_time]"] = min_time
        if max_time:
            params["filter[max_time]"] = max_time
        if route_id:
            params["filter[route]"] = route_id
        if stop_id:
            params["filter[stop]"] = stop_id
        if trip_id:
            params["filter[trip]"] = trip_id
        if direction_id is not None:
            params["filter[direction_id]"] = direction_id

        return await self._request("/schedules", params)
