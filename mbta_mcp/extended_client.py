"""Extended MBTA API along with additional IMT functionality and Massachusetts Amtrak vehicle data"""

import heapq
import json
import logging
import math
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any

from async_lru import alru_cache

from .client import MBTAClient
from .fuzzy_filter import filter_data_fuzzy

logger = logging.getLogger(__name__)

PAGE_LIMIT = 175
IMT_BASE_URL = "https://imt.ryanwallace.cloud"
AMTRAK_BASE_URL = "https://bos.ryanwallace.cloud"

# Major transfer stations for multi-line connections
MAJOR_TRANSFER_STATIONS = {
    # Downtown transfer hub - Red/Green/Blue/Orange
    "place-dtnxg": {  # Downtown Crossing
        "name": "Downtown Crossing",
        "lines": ["Red", "Orange"],
        "transfer_walking_minutes": 2,
    },
    "place-pktrm": {  # Park Street
        "name": "Park Street",
        "lines": ["Red", "Green-B", "Green-C", "Green-D", "Green-E"],
        "transfer_walking_minutes": 3,
    },
    "place-state": {  # State
        "name": "State",
        "lines": ["Blue", "Orange"],
        "transfer_walking_minutes": 2,
    },
    "place-gover": {  # Government Center
        "name": "Government Center",
        "lines": ["Blue", "Green-B", "Green-C", "Green-D", "Green-E"],
        "transfer_walking_minutes": 3,
    },
    # Other important transfer points
    "place-north": {  # North Station
        "name": "North Station",
        "lines": ["Green-C", "Green-E", "Orange"],
        "transfer_walking_minutes": 3,
    },
    "place-bbsta": {  # Back Bay
        "name": "Back Bay",
        "lines": ["Orange", "Commuter Rail"],
        "transfer_walking_minutes": 3,
    },
    "place-rugg": {  # Ruggles
        "name": "Ruggles",
        "lines": ["Orange", "Commuter Rail"],
        "transfer_walking_minutes": 2,
    },
    "place-forhl": {  # Forest Hills
        "name": "Forest Hills",
        "lines": ["Orange", "Commuter Rail"],
        "transfer_walking_minutes": 3,
    },
}


class ExtendedMBTAClient(MBTAClient):
    """Extended client with all MBTA V3 API endpoints."""

    async def __aenter__(self) -> "ExtendedMBTAClient":
        await super().__aenter__()
        return self

    @alru_cache(maxsize=100, ttl=10)
    async def get_vehicle_positions(self) -> dict[str, Any]:
        """Get real-time vehicle positions from my IMT API."""
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        url = f"{IMT_BASE_URL}/vehicles"

        async with self.session.get(url) as response:
            response.raise_for_status()
            result: dict[str, Any] = await response.json()

            return result

    async def get_external_alerts(self) -> dict[str, Any]:
        """Get general alerts from the IMT API."""
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        url = f"{IMT_BASE_URL}/alerts"

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

        url = f"{IMT_BASE_URL}/predictions"
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

        url = f"{IMT_BASE_URL}/chained-predictions"
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

        url = f"{IMT_BASE_URL}/stats/{station_id}/{route_id}"

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

        url = f"{IMT_BASE_URL}/historical/{station_id}/{route_id}"
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

        url = f"{AMTRAK_BASE_URL}/trains"

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

        url = f"{AMTRAK_BASE_URL}/trains/geojson"

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

        url = f"{AMTRAK_BASE_URL}/health"

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

        First checks against major_stations.json for better performance and accuracy.
        Falls back to MBTA API search if needed.
        """
        # First, search in major stations data
        major_stations_matches = await self._search_major_stations(
            query, latitude, longitude, radius, page_limit
        )
        
        # If we found good matches in major stations, return them
        if major_stations_matches and len(major_stations_matches) >= min(3, page_limit):
            return {
                "data": major_stations_matches,
                "meta": {
                    "source": "major_stations.json",
                    "total": len(major_stations_matches)
                }
            }
        
        # Fall back to API search if needed
        params: dict[str, Any] = {
            "page[limit]": min(page_limit * 10, PAGE_LIMIT),
        }

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
        # Since MBTA API geographic filtering is unreliable, fetch a larger set
        # and filter client-side by actual distance
        params: dict[str, Any] = {
            "page[limit]": PAGE_LIMIT,  # Fetch maximum to ensure we get nearby stops
        }
        result = await self._request("/stops", params)

        # Filter by actual distance client-side since MBTA API geographic filtering is unreliable
        if "data" in result:
            nearby_stops = []
            radius_km = radius / 1000  # Convert to kilometers

            for stop in result["data"]:
                stop_lat = stop["attributes"]["latitude"]
                stop_lon = stop["attributes"]["longitude"]

                # If stop doesn't have coordinates, try to get them from parent station
                if not stop_lat or not stop_lon:
                    parent_station = (
                        stop.get("relationships", {})
                        .get("parent_station", {})
                        .get("data")
                    )
                    if parent_station:
                        try:
                            parent_id = parent_station.get("id")
                            parent_result = await self._request(
                                f"/stops/{parent_id}", {}
                            )
                            if parent_result.get("data"):
                                parent_data = parent_result["data"]
                                stop_lat = parent_data["attributes"]["latitude"]
                                stop_lon = parent_data["attributes"]["longitude"]
                                if stop_lat and stop_lon:
                                    # Update the stop data with parent coordinates
                                    stop["attributes"]["latitude"] = stop_lat
                                    stop["attributes"]["longitude"] = stop_lon
                                    stop["_from_parent"] = True  # Mark for debugging
                        except Exception:
                            continue  # Skip if can't get parent data

                # Skip if still no coordinates
                if not stop_lat or not stop_lon:
                    continue

                stop_lat = float(stop_lat)
                stop_lon = float(stop_lon)

                distance_km = self._haversine_distance(
                    latitude, longitude, stop_lat, stop_lon
                )

                if distance_km <= radius_km:
                    # Add distance info for sorting
                    stop["_distance_km"] = distance_km
                    nearby_stops.append(stop)

            # Sort by distance and limit results
            nearby_stops.sort(key=lambda x: x["_distance_km"])
            result["data"] = nearby_stops[:page_limit]

        return result

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
        result = await self._request(
            "/stops",
            {
                "page[limit]": PAGE_LIMIT,
            },
        )

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

    async def plan_trip(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        departure_time: str | None = None,
        arrival_time: str | None = None,
        max_walk_distance: float = 800,
        max_transfers: int = 3,
        prefer_fewer_transfers: bool = True,
        wheelchair_accessible: bool = False,
    ) -> dict[str, Any]:
        """Plan a trip between two locations using MBTA services.

        Args:
            origin_lat: Origin latitude
            origin_lon: Origin longitude
            dest_lat: Destination latitude
            dest_lon: Destination longitude
            departure_time: Preferred departure time (ISO format, defaults to now)
            arrival_time: Required arrival time (ISO format, overrides departure_time)
            max_walk_distance: Maximum walking distance in meters (default: 800)
            max_transfers: Maximum number of transfers allowed (default: 3)
            prefer_fewer_transfers: Prioritize routes with fewer transfers (default: True)
            wheelchair_accessible: Only include wheelchair accessible routes (default: False)

        Returns:
            Dict containing trip options with routes, times, transfers, and walking directions
        """
        # Constants
        max_stops_limit = 10

        try:
            # Check for service alerts that might affect trip planning
            service_alerts = await self._get_relevant_service_alerts(
                origin_lat, origin_lon, dest_lat, dest_lon
            )

            # Find nearby stops for origin and destination with progressive search radii
            origin_stops = await self._find_nearby_transit_stops(
                origin_lat, origin_lon, max_walk_distance, max_stops_limit, wheelchair_accessible
            )
            dest_stops = await self._find_nearby_transit_stops(
                dest_lat, dest_lon, max_walk_distance, max_stops_limit, wheelchair_accessible
            )

            if not origin_stops.get("data") or not dest_stops.get("data"):
                return {
                    "error": "No transit stops found within walking distance",
                    "origin_stops_found": len(origin_stops.get("data", [])),
                    "dest_stops_found": len(dest_stops.get("data", [])),
                    "service_alerts": service_alerts,
                }

            # Set default departure time to now if not specified
            if not departure_time and not arrival_time:
                departure_time = datetime.now().astimezone().isoformat()

            # Plan routes using graph search algorithm
            trip_options = await self._find_optimal_routes(
                origin_stops["data"],
                dest_stops["data"],
                (origin_lat, origin_lon),
                (dest_lat, dest_lon),
                departure_time,
                arrival_time,
                max_transfers,
                prefer_fewer_transfers,
                wheelchair_accessible,
                service_alerts,
            )

            # If no routes found and there are service alerts, try alternative planning
            if not trip_options and service_alerts:
                trip_options = await self._plan_alternative_routes_with_alerts(
                    origin_stops["data"],
                    dest_stops["data"],
                    (origin_lat, origin_lon),
                    (dest_lat, dest_lon),
                    departure_time,
                    arrival_time,
                    max_transfers,
                    prefer_fewer_transfers,
                    wheelchair_accessible,
                    service_alerts,
                )

            # If still no routes found, suggest alternative modes
            if not trip_options:
                alternative_modes = self._suggest_alternative_modes(
                    (origin_lat, origin_lon),
                    (dest_lat, dest_lon),
                    service_alerts,
                    wheelchair_accessible,
                )
                
                if alternative_modes:
                    trip_options = [{
                        "type": "alternative_modes",
                        "message": "No transit routes available. Consider these alternatives:",
                        "alternatives": alternative_modes,
                        "reason": "service_disruption" if service_alerts else "no_routes_found"
                    }]

        except Exception as e:
            logger.exception("Trip planning failed")
            return {"error": f"Trip planning failed: {e!s}"}
        else:
            return {
                "origin": {"lat": origin_lat, "lon": origin_lon},
                "destination": {"lat": dest_lat, "lon": dest_lon},
                "trip_options": trip_options,
                "service_alerts": service_alerts,
                "search_parameters": {
                    "departure_time": departure_time,
                    "arrival_time": arrival_time,
                    "max_walk_distance": max_walk_distance,
                    "max_transfers": max_transfers,
                    "prefer_fewer_transfers": prefer_fewer_transfers,
                    "wheelchair_accessible": wheelchair_accessible,
                },
            }

    async def _get_relevant_service_alerts(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> list[dict[str, Any]]:
        """Get service alerts that might affect trip planning between two locations."""
        try:
            # Get all active alerts
            all_alerts = await self.list_all_alerts(max_results=100)
            relevant_alerts: list[dict[str, Any]] = []

            if not all_alerts.get("data"):
                return relevant_alerts

            # Check each alert for relevance to the trip
            for alert in all_alerts["data"]:
                if self._is_alert_relevant_to_trip(alert, origin_lat, origin_lon, dest_lat, dest_lon):
                    relevant_alerts.append(alert)

            return relevant_alerts

        except Exception as e:
            logger.warning(f"Failed to get service alerts: {e}")
            return []

    def _is_alert_relevant_to_trip(
        self,
        alert: dict[str, Any],
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> bool:
        """Check if a service alert is relevant to the planned trip."""
        try:
            # Check if alert is active
            if alert.get("attributes", {}).get("lifecycle") != "ONGOING":
                return False

            # Check severity (high severity alerts are more relevant)
            severity = alert.get("attributes", {}).get("severity", 0)
            if severity >= 5:  # High severity alerts
                return True

            # Check if alert affects major routes or stations
            informed_entities = alert.get("attributes", {}).get("informed_entity", [])
            
            # Major routes that could affect the trip
            major_routes = {"Red", "Orange", "Blue", "Green-B", "Green-C", "Green-D", "Green-E"}
            
            for entity in informed_entities:
                route_id = entity.get("route")
                if route_id in major_routes:
                    return True

            return False

        except Exception as e:
            logger.warning(f"Error checking alert relevance: {e}")
            return False

    async def _plan_alternative_routes_with_alerts(
        self,
        origin_stops: list[dict[str, Any]],
        dest_stops: list[dict[str, Any]],
        origin_coords: tuple[float, float],
        dest_coords: tuple[float, float],
        departure_time: str | None,
        arrival_time: str | None,
        max_transfers: int,
        prefer_fewer_transfers: bool,
        wheelchair_accessible: bool,
        service_alerts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Plan alternative routes considering service alerts and disruptions."""
        try:
            # Extract affected routes from alerts
            affected_routes = set()
            for alert in service_alerts:
                informed_entities = alert.get("attributes", {}).get("informed_entity", [])
                for entity in informed_entities:
                    route_id = entity.get("route")
                    if route_id:
                        affected_routes.add(route_id)

            # Filter out stops that are on affected routes
            filtered_origin_stops = [
                stop for stop in origin_stops
                if not self._is_stop_affected_by_alerts(stop, affected_routes)
            ]
            filtered_dest_stops = [
                stop for stop in dest_stops
                if not self._is_stop_affected_by_alerts(stop, affected_routes)
            ]

            # If we still have stops, try planning with filtered stops
            if filtered_origin_stops and filtered_dest_stops:
                return await self._find_optimal_routes(
                    filtered_origin_stops,
                    filtered_dest_stops,
                    origin_coords,
                    dest_coords,
                    departure_time,
                    arrival_time,
                    max_transfers,
                    prefer_fewer_transfers,
                    wheelchair_accessible,
                )

            # If no routes found, return a helpful message
            return [{
                "type": "service_disruption",
                "message": "No accessible routes found due to service disruptions",
                "affected_routes": list(affected_routes),
                "suggestions": [
                    "Consider traveling at a different time",
                    "Check MBTA.com for shuttle bus information",
                    "Consider alternative transportation options"
                ]
            }]

        except Exception as e:
            logger.warning(f"Alternative route planning failed: {e}")
            return []

    def _is_stop_affected_by_alerts(
        self,
        stop: dict[str, Any],
        affected_routes: set[str]
    ) -> bool:
        """Check if a stop is affected by service alerts."""
        try:
            # Get routes that serve this stop
            stop_id = stop.get("id", "")
            
            # Check if this stop is on any affected routes
            # This is a simplified check - in a full implementation,
            # we'd need to get the actual routes that serve this stop
            for route_id in affected_routes:
                if route_id.lower() in stop_id.lower():
                    return True
                    
            return False

        except Exception as e:
            logger.warning(f"Error checking if stop is affected: {e}")
            return False

    def _suggest_alternative_modes(
        self,
        origin_coords: tuple[float, float],
        dest_coords: tuple[float, float],
        service_alerts: list[dict[str, Any]],
        wheelchair_accessible: bool = False,
    ) -> list[dict[str, Any]]:
        """Suggest alternative transportation modes when transit is disrupted."""
        try:
            origin_lat, origin_lon = origin_coords
            dest_lat, dest_lon = dest_coords
            
            # Calculate direct distance
            direct_distance_km = self._haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
            direct_distance_miles = direct_distance_km * 0.621371
            
            suggestions = []
            
            # Walking suggestion (if distance is reasonable)
            if direct_distance_km <= 3.0:  # 3 km or less
                walk_time_minutes = int(direct_distance_km * 12)  # 5 km/h walking speed
                suggestions.append({
                    "mode": "walking",
                    "description": f"Walk {direct_distance_miles:.1f} miles",
                    "duration_minutes": walk_time_minutes,
                    "distance_km": direct_distance_km,
                    "accessibility": "wheelchair_accessible" if wheelchair_accessible else "check_route",
                    "cost": "free",
                    "reliability": "high",
                    "suitable_for": ["short_trips", "exercise", "no_baggage"]
                })
            
            # Biking suggestion (if distance is reasonable)
            if 1.0 <= direct_distance_km <= 15.0:  # 1-15 km
                bike_time_minutes = int(direct_distance_km * 4)  # 15 km/h biking speed
                suggestions.append({
                    "mode": "biking",
                    "description": f"Bike {direct_distance_miles:.1f} miles",
                    "duration_minutes": bike_time_minutes,
                    "distance_km": direct_distance_km,
                    "accessibility": "requires_bike" if not wheelchair_accessible else "not_suitable",
                    "cost": "free",
                    "reliability": "high",
                    "suitable_for": ["medium_trips", "exercise", "no_baggage"]
                })
            
            # Rideshare suggestion (for longer distances or when transit is disrupted)
            if direct_distance_km > 2.0:
                # Estimate rideshare cost (rough approximation)
                base_fare = 2.50
                per_mile_rate = 1.50
                estimated_cost = base_fare + (direct_distance_miles * per_mile_rate)
                
                suggestions.append({
                    "mode": "rideshare",
                    "description": f"Rideshare {direct_distance_miles:.1f} miles",
                    "duration_minutes": int(direct_distance_km * 2.5),  # 24 km/h average speed
                    "distance_km": direct_distance_km,
                    "accessibility": "wheelchair_accessible" if wheelchair_accessible else "standard",
                    "cost": f"${estimated_cost:.2f}",
                    "reliability": "high",
                    "suitable_for": ["any_distance", "baggage", "comfort"]
                })
            
            # Taxi suggestion
            if direct_distance_km > 1.0:
                taxi_cost = 3.00 + (direct_distance_miles * 2.00)
                suggestions.append({
                    "mode": "taxi",
                    "description": f"Taxi {direct_distance_miles:.1f} miles",
                    "duration_minutes": int(direct_distance_km * 2.5),
                    "distance_km": direct_distance_km,
                    "accessibility": "wheelchair_accessible" if wheelchair_accessible else "standard",
                    "cost": f"${taxi_cost:.2f}",
                    "reliability": "medium",
                    "suitable_for": ["any_distance", "baggage", "comfort"]
                })
            
            # Commuter rail alternative (if available)
            if self._has_commuter_rail_alternative(origin_coords, dest_coords, service_alerts):
                suggestions.append({
                    "mode": "commuter_rail",
                    "description": "Use commuter rail as alternative",
                    "duration_minutes": None,  # Will be calculated by trip planning
                    "distance_km": direct_distance_km,
                    "accessibility": "wheelchair_accessible" if wheelchair_accessible else "check_station",
                    "cost": "$2.40-13.25",
                    "reliability": "medium",
                    "suitable_for": ["longer_trips", "baggage", "comfort"]
                })
            
            return suggestions

        except Exception as e:
            logger.warning(f"Error suggesting alternative modes: {e}")
            return []

    def _has_commuter_rail_alternative(
        self,
        origin_coords: tuple[float, float],
        dest_coords: tuple[float, float],
        service_alerts: list[dict[str, Any]]
    ) -> bool:
        """Check if commuter rail is available as an alternative."""
        try:
            # Check if any commuter rail routes are affected by alerts
            affected_commuter_routes = set()
            for alert in service_alerts:
                informed_entities = alert.get("attributes", {}).get("informed_entity", [])
                for entity in informed_entities:
                    route_id = entity.get("route")
                    if route_id and route_id.startswith("CR-"):
                        affected_commuter_routes.add(route_id)
            
            # If no commuter rail alerts, it might be available
            return len(affected_commuter_routes) == 0
            
        except Exception as e:
            logger.warning(f"Error checking commuter rail alternatives: {e}")
            return False

    async def _find_optimal_routes(
        self,
        origin_stops: list[dict[str, Any]],
        dest_stops: list[dict[str, Any]],
        origin_coords: tuple[float, float],
        dest_coords: tuple[float, float],
        departure_time: str | None,
        _arrival_time: str | None,
        max_transfers: int,
        prefer_fewer_transfers: bool,
        wheelchair_accessible: bool,
        service_alerts: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Find optimal routes including direct routes and routes with transfers."""
        all_routes: list[dict[str, Any]] = []

        # For each origin stop, find best routes to destination
        for origin_stop in origin_stops[:5]:  # Limit to top 5 closest origin stops
            origin_walk_time = self._calculate_walk_time(
                origin_coords,
                (
                    float(origin_stop["attributes"]["latitude"]),
                    float(origin_stop["attributes"]["longitude"]),
                ),
            )

            try:
                # Get real-time predictions for this origin stop
                origin_data = await self.get_predictions_for_stop(
                    origin_stop["id"], page_limit=50
                )

                if not origin_data.get("data"):
                    continue

                # 1. Find direct routes to destination stops
                direct_routes = await self._find_direct_routes(
                    origin_stop,
                    dest_stops,
                    origin_data["data"],
                    departure_time,
                    wheelchair_accessible,
                )

                # Format direct routes
                for route_option in direct_routes:
                    dest_walk_time = self._calculate_walk_time(
                        dest_coords,
                        (
                            float(route_option["final_stop"]["attributes"]["latitude"]),
                            float(
                                route_option["final_stop"]["attributes"]["longitude"]
                            ),
                        ),
                    )

                    route_option.update(
                        {
                            "origin_walk_minutes": origin_walk_time,
                            "dest_walk_minutes": dest_walk_time,
                            "total_time_minutes": (
                                origin_walk_time
                                + route_option["transit_time_minutes"]
                                + dest_walk_time
                            ),
                        }
                    )

                all_routes.extend(direct_routes)

                # 2. Find routes with transfers if max_transfers > 0 and no direct routes found
                if max_transfers > 0 and len(direct_routes) == 0:
                    transfer_routes = await self._find_simplified_transfer_routes(
                        origin_stop,
                        dest_stops,
                        origin_data["data"],
                        departure_time,
                        wheelchair_accessible,
                        origin_walk_time,
                        dest_coords,
                        service_alerts,
                    )
                    all_routes.extend(transfer_routes)

            except Exception as e:
                logger.warning(
                    "Failed to get data for stop %s: %s", origin_stop["id"], e
                )
                continue

        # Remove duplicates and sort routes
        unique_routes = self._deduplicate_routes(all_routes)

        if prefer_fewer_transfers:
            unique_routes.sort(
                key=lambda x: (x["num_transfers"], x["total_time_minutes"])
            )
        else:
            unique_routes.sort(key=lambda x: x["total_time_minutes"])

        return unique_routes[:5]  # Return top 5 routes

    async def _find_direct_routes(
        self,
        origin_stop: dict[str, Any],
        dest_stops: list[dict[str, Any]],
        origin_departures: list[dict[str, Any]],
        departure_time: str | None,
        wheelchair_accessible: bool,
    ) -> list[dict[str, Any]]:
        """Find direct routes from origin to destination stops."""
        routes_found: list[dict[str, Any]] = []
        dest_stop_ids = {stop["id"] for stop in dest_stops}

        # Check each departure from origin
        for departure in origin_departures[:3]:  # Reduce API load  # Limit departures
            if wheelchair_accessible and not departure.get("attributes", {}).get(
                "wheelchair_accessible"
            ):
                continue

            departure_datetime = self._parse_datetime(
                departure.get("attributes", {}).get("departure_time")
                or departure.get("attributes", {}).get("arrival_time")
            )

            if not departure_datetime:
                continue

            # Check if this departure is after our desired departure time
            if departure_time:
                desired_dt = self._parse_datetime(departure_time)
                if desired_dt and departure_datetime < desired_dt:
                    continue

            # Get trip details to see all stops on this trip
            trip_id = (
                departure.get("relationships", {})
                .get("trip", {})
                .get("data", {})
                .get("id")
            )
            if not trip_id:
                continue

            try:
                # Get schedules for this trip directly
                schedules_data = await self.get_schedules(
                    trip_id=trip_id, page_limit=50
                )
                if not schedules_data.get("data"):
                    continue

                schedules = schedules_data["data"]

                origin_found = False
                for schedule in schedules:
                    stop_id = (
                        schedule.get("relationships", {})
                        .get("stop", {})
                        .get("data", {})
                        .get("id")
                    )

                    # Mark when we find origin stop
                    if stop_id == origin_stop["id"]:
                        origin_found = True
                        continue

                    # Check for destination stops after origin
                    if origin_found and stop_id in dest_stop_ids:
                        arrival_time_str = schedule.get("attributes", {}).get(
                            "arrival_time"
                        )
                        if arrival_time_str:
                            arrival_datetime = self._parse_datetime(arrival_time_str)
                            if (
                                arrival_datetime
                                and arrival_datetime > departure_datetime
                            ):
                                travel_time = int(
                                    (
                                        arrival_datetime - departure_datetime
                                    ).total_seconds()
                                    / 60
                                )

                                final_stop = next(
                                    stop for stop in dest_stops if stop["id"] == stop_id
                                )
                                routes_found.append(
                                    {
                                        "route_path": [
                                            {
                                                "stop": origin_stop,
                                                "departure": departure,
                                                "route_id": departure.get(
                                                    "relationships", {}
                                                )
                                                .get("route", {})
                                                .get("data", {})
                                                .get("id"),
                                                "trip_id": trip_id,
                                                "departure_time": departure_datetime.isoformat(),
                                                "arrival_time": arrival_datetime.isoformat(),
                                            }
                                        ],
                                        "final_stop": final_stop,
                                        "transit_time_minutes": travel_time,
                                        "num_transfers": 0,
                                        "arrival_time": arrival_datetime.isoformat(),
                                    }
                                )
                                break  # Found a destination, move to next departure

            except Exception as e:
                logger.debug("Failed to get trip details for %s: %s", trip_id, e)
                continue

        return routes_found[:5]

    async def _find_transfer_routes(
        self,
        origin_stop: dict[str, Any],
        dest_stops: list[dict[str, Any]],
        origin_departures: list[dict[str, Any]],
        departure_time: str | None,
        _max_transfers: int,
        wheelchair_accessible: bool,
        origin_walk_time: int,
        dest_coords: tuple[float, float],
        service_alerts: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Find routes that require transfers through major transfer stations."""
        transfer_routes: list[dict[str, Any]] = []

        # Get the route/line that serves the origin stop
        origin_routes = set()
        for departure in origin_departures[:3]:  # Reduce API load
            route_id = (
                departure.get("relationships", {})
                .get("route", {})
                .get("data", {})
                .get("id")
            )
            if route_id:
                origin_routes.add(route_id)

        if not origin_routes:
            return transfer_routes

        # Find potential transfer stations that connect origin routes to destination routes
        potential_transfers = self._find_transfer_stations(origin_routes, dest_stops, service_alerts)

        # For each potential transfer, try to build a route
        for transfer_station_id, transfer_info in potential_transfers.items():
            try:
                # Find routes from origin to transfer station
                first_leg_routes = await self._find_routes_to_transfer(
                    origin_stop,
                    transfer_station_id,
                    origin_departures,
                    departure_time,
                    wheelchair_accessible,
                )

                if not first_leg_routes:
                    continue

                # For each first leg route, find connecting routes to destination
                for first_leg in first_leg_routes[:3]:  # Limit to top 3 first legs
                    arrival_at_transfer = first_leg["arrival_time"]
                    transfer_walk_time = transfer_info["transfer_walking_minutes"]

                    # Get predictions at transfer station for connecting routes
                    connection_departures = await self.get_predictions_for_stop(
                        transfer_station_id, page_limit=30
                    )

                    if not connection_departures.get("data"):
                        continue

                    # Find routes from transfer to destination
                    second_leg_routes = await self._find_routes_from_transfer(
                        transfer_station_id,
                        dest_stops,
                        connection_departures["data"],
                        arrival_at_transfer,
                        transfer_walk_time,
                        wheelchair_accessible,
                        dest_coords,
                    )

                    # Combine first and second legs into complete routes
                    for second_leg in second_leg_routes[:2]:  # Top 2 second legs
                        complete_route = self._combine_route_legs(
                            first_leg, second_leg, transfer_info, origin_walk_time
                        )

                        if complete_route:
                            transfer_routes.append(complete_route)

            except Exception as e:
                logger.debug(
                    "Failed to find transfer route via %s: %s", transfer_station_id, e
                )
                continue

        return transfer_routes[:10]  # Return top 10 transfer routes

    async def _find_simplified_transfer_routes(
        self,
        origin_stop: dict[str, Any],
        dest_stops: list[dict[str, Any]],
        origin_departures: list[dict[str, Any]],
        departure_time: str | None,
        _wheelchair_accessible: bool,
        origin_walk_time: int,
        dest_coords: tuple[float, float],
        service_alerts: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Find transfer routes using simplified timing estimates."""
        simplified_routes: list[dict[str, Any]] = []

        # Get origin routes
        origin_routes = set()
        for departure in origin_departures[:3]:
            route_id = (
                departure.get("relationships", {})
                .get("route", {})
                .get("data", {})
                .get("id")
            )
            if route_id:
                origin_routes.add(route_id)

        if not origin_routes:
            return simplified_routes

        # Find potential transfers
        potential_transfers = self._find_transfer_stations(origin_routes, dest_stops, service_alerts)

        if not potential_transfers:
            return simplified_routes

        # Create simplified transfer routes using estimated timing
        for departure in origin_departures[:2]:  # Only use first 2 departures
            departure_datetime = self._parse_datetime(
                departure.get("attributes", {}).get("departure_time")
                or departure.get("attributes", {}).get("arrival_time")
            )

            if not departure_datetime:
                continue

            # Check departure time constraint
            if departure_time:
                desired_dt = self._parse_datetime(departure_time)
                if desired_dt and departure_datetime < desired_dt:
                    continue

            route_id = (
                departure.get("relationships", {})
                .get("route", {})
                .get("data", {})
                .get("id")
            )

            # For each potential transfer station, create estimated route
            for _transfer_station_id, transfer_info in list(
                potential_transfers.items()
            )[:2]:  # Limit transfers
                # Estimate timing based on typical MBTA travel times
                estimated_times = self._estimate_transfer_timing(
                    origin_stop["attributes"]["name"],
                    transfer_info["name"],
                    dest_stops[0]["attributes"]["name"],  # Use closest dest stop
                    route_id,
                )

                if estimated_times:
                    # Calculate final arrival time
                    first_leg_minutes = estimated_times["first_leg_minutes"]
                    transfer_minutes = transfer_info["transfer_walking_minutes"]
                    second_leg_minutes = estimated_times["second_leg_minutes"]

                    arrival_at_transfer = departure_datetime + timedelta(
                        minutes=first_leg_minutes
                    )
                    departure_from_transfer = arrival_at_transfer + timedelta(
                        minutes=transfer_minutes
                    )
                    final_arrival = departure_from_transfer + timedelta(
                        minutes=second_leg_minutes
                    )

                    # Calculate destination walking time
                    dest_walk_time = self._calculate_walk_time(
                        dest_coords,
                        (
                            float(dest_stops[0]["attributes"]["latitude"]),
                            float(dest_stops[0]["attributes"]["longitude"]),
                        ),
                    )

                    # Create simplified route
                    simplified_route = {
                        "route_path": [
                            {
                                "route_id": route_id,
                                "departure_time": departure_datetime.isoformat(),
                                "arrival_time": arrival_at_transfer.isoformat(),
                                "leg_type": "transit",
                                "estimated": True,
                            },
                            {
                                "transfer_station": transfer_info["name"],
                                "transfer_walking_minutes": transfer_minutes,
                                "leg_type": "transfer",
                            },
                            {
                                "route_id": estimated_times["second_route"],
                                "departure_time": departure_from_transfer.isoformat(),
                                "arrival_time": final_arrival.isoformat(),
                                "leg_type": "transit",
                                "estimated": True,
                            },
                        ],
                        "final_stop": dest_stops[0],
                        "transit_time_minutes": first_leg_minutes
                        + transfer_minutes
                        + second_leg_minutes,
                        "num_transfers": 1,
                        "arrival_time": final_arrival.isoformat(),
                        "origin_walk_minutes": origin_walk_time,
                        "dest_walk_minutes": dest_walk_time,
                        "total_time_minutes": (
                            origin_walk_time
                            + first_leg_minutes
                            + transfer_minutes
                            + second_leg_minutes
                            + dest_walk_time
                        ),
                        "estimated": True,
                    }

                    simplified_routes.append(simplified_route)

        return simplified_routes[:3]  # Return top 3 simplified routes

    def _estimate_transfer_timing(
        self, origin_name: str, transfer_name: str, dest_name: str, origin_route: str
    ) -> dict[str, Any] | None:
        """Estimate travel times for transfer routes using typical MBTA timing."""

        # Common transfer scenarios with estimated times (in minutes)
        transfer_scenarios = {
            # Red Line to Green Line via Park Street
            ("Red", "Park Street", "Green"): {
                "kendall_to_park": 4,
                "central_to_park": 2,
                "park_to_copley": 3,
                "park_to_hynes": 5,
            },
            # Red Line to Green Line via Downtown Crossing (indirect)
            ("Red", "Downtown Crossing", "Green"): {
                "kendall_to_downtown": 6,
                "central_to_downtown": 4,
                "downtown_to_copley": 8,  # Via State/Government Center
                "downtown_to_hynes": 10,
            },
        }

        # Find matching scenario
        scenario_key = (origin_route, transfer_name, "Green")
        if scenario_key not in transfer_scenarios:
            # Use generic estimates
            return {
                "first_leg_minutes": 5,
                "second_leg_minutes": 6,
                "second_route": "Green-B",  # Default Green Line
            }

        timing_data = transfer_scenarios[scenario_key]

        # Estimate first leg (origin to transfer)
        origin_lower = origin_name.lower()
        first_leg = 5  # Default
        if "kendall" in origin_lower and "park" in timing_data:
            first_leg = timing_data.get("kendall_to_park", 5)
        elif "central" in origin_lower and "park" in timing_data:
            first_leg = timing_data.get("central_to_park", 5)
        elif "kendall" in origin_lower and "downtown" in timing_data:
            first_leg = timing_data.get("kendall_to_downtown", 6)
        elif "central" in origin_lower and "downtown" in timing_data:
            first_leg = timing_data.get("central_to_downtown", 4)

        # Estimate second leg (transfer to destination)
        dest_lower = dest_name.lower()
        second_leg = 6  # Default
        second_route = "Green-B"

        if "copley" in dest_lower:
            second_leg = (
                timing_data.get("park_to_copley", 3)
                if "park" in timing_data
                else timing_data.get("downtown_to_copley", 8)
            )
            second_route = "Green-B"
        elif "hynes" in dest_lower:
            second_leg = (
                timing_data.get("park_to_hynes", 5)
                if "park" in timing_data
                else timing_data.get("downtown_to_hynes", 10)
            )
            second_route = "Green-B"

        return {
            "first_leg_minutes": first_leg,
            "second_leg_minutes": second_leg,
            "second_route": second_route,
        }

    def _find_transfer_stations(
        self, 
        origin_routes: set[str], 
        dest_stops: list[dict[str, Any]],
        service_alerts: list[dict[str, Any]] | None = None
    ) -> dict[str, dict[str, Any]]:
        """Find optimal transfer stations between origin and destination routes."""
        transfer_stations = {}
        
        service_alerts = service_alerts or []

        # Get destination routes by checking what lines serve destination stops
        dest_routes = set()
        for stop in dest_stops:
            # Infer route from stop attributes or use fuzzy matching
            stop_name = stop["attributes"]["name"].lower()
            if any(color in stop_name for color in ["red", "blue", "orange"]):
                if "red" in stop_name:
                    dest_routes.add("Red")
                elif "blue" in stop_name:
                    dest_routes.add("Blue")
                elif "orange" in stop_name:
                    dest_routes.add("Orange")
            else:
                # Assume Green Line for other rapid transit
                dest_routes.update(["Green-B", "Green-C", "Green-D", "Green-E"])

        # Get affected routes from service alerts
        affected_routes = set()
        for alert in service_alerts:
            informed_entities = alert.get("attributes", {}).get("informed_entity", [])
            for entity in informed_entities:
                route_id = entity.get("route")
                if route_id:
                    affected_routes.add(route_id)

        # Find transfer stations that connect origin and destination routes
        for transfer_id, transfer_info in MAJOR_TRANSFER_STATIONS.items():
            transfer_routes = (
                set(transfer_info["lines"])
                if isinstance(transfer_info["lines"], list)
                else set()
            )

            # Check if this transfer station can connect origin to destination
            if (origin_routes & transfer_routes) and (dest_routes & transfer_routes):
                # Skip if either route is affected by service alerts
                if (origin_routes & affected_routes) or (dest_routes & affected_routes):
                    continue
                    
                # Check if this transfer station is affected by alerts
                if not self._is_transfer_station_affected(transfer_id, service_alerts):
                    transfer_stations[transfer_id] = {
                        "name": transfer_info["name"],
                        "lines": transfer_info["lines"],
                        "transfer_walking_minutes": transfer_info["transfer_walking_minutes"],
                        "reliability": self._assess_transfer_reliability(transfer_id, origin_routes, dest_routes, service_alerts),
                        "accessibility": self._assess_transfer_accessibility(transfer_id),
                    }

        # Sort transfer stations by reliability and accessibility
        sorted_transfers = dict(sorted(
            transfer_stations.items(),
            key=lambda x: (
                x[1]["reliability"],
                x[1]["accessibility"],
                x[1]["transfer_walking_minutes"]
            ),
            reverse=True
        ))

        return sorted_transfers

    def _is_transfer_station_affected(
        self, 
        station_id: str, 
        service_alerts: list[dict[str, Any]]
    ) -> bool:
        """Check if a transfer station is affected by service alerts."""
        try:
            for alert in service_alerts:
                informed_entities = alert.get("attributes", {}).get("informed_entity", [])
                for entity in informed_entities:
                    stop_id = entity.get("stop")
                    if stop_id and stop_id == station_id:
                        return True
            return False
        except Exception as e:
            logger.warning(f"Error checking if transfer station is affected: {e}")
            return False

    def _assess_transfer_reliability(
        self, 
        station_id: str, 
        origin_routes: set[str], 
        dest_routes: set[str], 
        service_alerts: list[dict[str, Any]]
    ) -> float:
        """Assess the reliability of a transfer station (0.0 to 1.0)."""
        try:
            reliability = 1.0
            
            # Check for alerts affecting this station
            for alert in service_alerts:
                informed_entities = alert.get("attributes", {}).get("informed_entity", [])
                for entity in informed_entities:
                    stop_id = entity.get("stop")
                    if stop_id and stop_id == station_id:
                        # Reduce reliability based on alert severity
                        severity = alert.get("attributes", {}).get("severity", 1)
                        if severity >= 7:  # High severity
                            reliability -= 0.5
                        elif severity >= 5:  # Medium severity
                            reliability -= 0.3
                        else:  # Low severity
                            reliability -= 0.1
            
            # Boost reliability for major transfer hubs
            if station_id in ["place-dtnxg", "place-pktrm", "place-state", "place-gover"]:
                reliability += 0.1
            
            return max(0.0, min(1.0, reliability))
            
        except Exception as e:
            logger.warning(f"Error assessing transfer reliability: {e}")
            return 0.5

    def _assess_transfer_accessibility(self, station_id: str) -> str:
        """Assess the accessibility of a transfer station."""
        try:
            # Major transfer stations are generally more accessible
            major_stations = ["place-dtnxg", "place-pktrm", "place-state", "place-gover", "place-north", "place-sstat"]
            
            if station_id in major_stations:
                return "high"
            else:
                return "medium"
                
        except Exception as e:
            logger.warning(f"Error assessing transfer accessibility: {e}")
            return "unknown"

    async def _find_routes_to_transfer(
        self,
        origin_stop: dict[str, Any],
        transfer_station_id: str,
        origin_departures: list[dict[str, Any]],
        departure_time: str | None,
        wheelchair_accessible: bool,
    ) -> list[dict[str, Any]]:
        """Find routes from origin stop to a transfer station."""
        routes_to_transfer = []

        for departure in origin_departures[:3]:  # Reduce API load
            if wheelchair_accessible and not departure.get("attributes", {}).get(
                "wheelchair_accessible"
            ):
                continue

            departure_datetime = self._parse_datetime(
                departure.get("attributes", {}).get("departure_time")
                or departure.get("attributes", {}).get("arrival_time")
            )

            if not departure_datetime:
                continue

            # Check if this departure is after desired time
            if departure_time:
                desired_dt = self._parse_datetime(departure_time)
                if desired_dt and departure_datetime < desired_dt:
                    continue

            # Get trip details to see if it stops at the transfer station
            trip_id = (
                departure.get("relationships", {})
                .get("trip", {})
                .get("data", {})
                .get("id")
            )
            if not trip_id:
                continue

            try:
                # Get schedules for this trip directly
                schedules_response = await self._request(
                    "/schedules", {"filter[trip]": trip_id, "page[limit]": 50}
                )
                schedules = schedules_response.get("data", [])

                # Check if this trip goes to the transfer station
                origin_found = False
                for schedule in schedules:
                    stop_id = (
                        schedule.get("relationships", {})
                        .get("stop", {})
                        .get("data", {})
                        .get("id")
                    )

                    if stop_id == origin_stop["id"]:
                        origin_found = True
                        continue

                    # Check if we reach the transfer station after origin
                    if origin_found and self._is_same_station(
                        stop_id, transfer_station_id
                    ):
                        arrival_time_str = schedule.get("attributes", {}).get(
                            "arrival_time"
                        )
                        if arrival_time_str:
                            arrival_datetime = self._parse_datetime(arrival_time_str)
                            if (
                                arrival_datetime
                                and arrival_datetime > departure_datetime
                            ):
                                travel_time = int(
                                    (
                                        arrival_datetime - departure_datetime
                                    ).total_seconds()
                                    / 60
                                )

                                routes_to_transfer.append(
                                    {
                                        "departure_time": departure_datetime.isoformat(),
                                        "arrival_time": arrival_datetime.isoformat(),
                                        "travel_time_minutes": travel_time,
                                        "route_id": departure.get("relationships", {})
                                        .get("route", {})
                                        .get("data", {})
                                        .get("id"),
                                        "trip_id": trip_id,
                                        "transfer_station_id": transfer_station_id,
                                    }
                                )
                                break

            except Exception as e:
                logger.debug("Failed to get trip details for %s: %s", trip_id, e)
                continue

        return routes_to_transfer

    async def _find_routes_from_transfer(
        self,
        transfer_station_id: str,
        dest_stops: list[dict[str, Any]],
        connection_departures: list[dict[str, Any]],
        arrival_at_transfer: str,
        transfer_walk_time: int,
        wheelchair_accessible: bool,
        dest_coords: tuple[float, float],
    ) -> list[dict[str, Any]]:
        """Find routes from transfer station to destination stops."""
        routes_from_transfer: list[dict[str, Any]] = []
        arrival_dt = self._parse_datetime(arrival_at_transfer)

        if not arrival_dt:
            return routes_from_transfer

        # Calculate earliest possible departure time (arrival + transfer walk time)
        earliest_departure = arrival_dt + timedelta(minutes=transfer_walk_time)
        dest_stop_ids = {stop["id"] for stop in dest_stops}

        for departure in connection_departures:
            if wheelchair_accessible and not departure.get("attributes", {}).get(
                "wheelchair_accessible"
            ):
                continue

            departure_datetime = self._parse_datetime(
                departure.get("attributes", {}).get("departure_time")
                or departure.get("attributes", {}).get("arrival_time")
            )

            if not departure_datetime or departure_datetime < earliest_departure:
                continue

            # Get trip details to check if it reaches destination
            trip_id = (
                departure.get("relationships", {})
                .get("trip", {})
                .get("data", {})
                .get("id")
            )
            if not trip_id:
                continue

            try:
                # Get schedules for this trip directly
                schedules_response = await self._request(
                    "/schedules", {"filter[trip]": trip_id, "page[limit]": 50}
                )
                schedules = schedules_response.get("data", [])

                # Find route to destination
                transfer_found = False
                for schedule in schedules:
                    stop_id = (
                        schedule.get("relationships", {})
                        .get("stop", {})
                        .get("data", {})
                        .get("id")
                    )

                    if self._is_same_station(stop_id, transfer_station_id):
                        transfer_found = True
                        continue

                    if transfer_found and stop_id in dest_stop_ids:
                        arrival_time_str = schedule.get("attributes", {}).get(
                            "arrival_time"
                        )
                        if arrival_time_str:
                            final_arrival = self._parse_datetime(arrival_time_str)
                            if final_arrival and final_arrival > departure_datetime:
                                travel_time = int(
                                    (final_arrival - departure_datetime).total_seconds()
                                    / 60
                                )

                                final_stop = next(
                                    stop for stop in dest_stops if stop["id"] == stop_id
                                )
                                dest_walk_time = self._calculate_walk_time(
                                    dest_coords,
                                    (
                                        float(final_stop["attributes"]["latitude"]),
                                        float(final_stop["attributes"]["longitude"]),
                                    ),
                                )

                                routes_from_transfer.append(
                                    {
                                        "departure_time": departure_datetime.isoformat(),
                                        "arrival_time": final_arrival.isoformat(),
                                        "travel_time_minutes": travel_time,
                                        "dest_walk_minutes": dest_walk_time,
                                        "route_id": departure.get("relationships", {})
                                        .get("route", {})
                                        .get("data", {})
                                        .get("id"),
                                        "trip_id": trip_id,
                                        "final_stop": final_stop,
                                    }
                                )
                                break

            except Exception as e:
                logger.debug("Failed to get trip details for %s: %s", trip_id, e)
                continue

        return routes_from_transfer

    def _combine_route_legs(
        self,
        first_leg: dict[str, Any],
        second_leg: dict[str, Any],
        transfer_info: dict[str, Any],
        origin_walk_time: int,
    ) -> dict[str, Any] | None:
        """Combine two route legs into a complete transfer route."""
        try:
            first_departure = self._parse_datetime(first_leg["departure_time"])
            first_arrival = self._parse_datetime(first_leg["arrival_time"])
            second_departure = self._parse_datetime(second_leg["departure_time"])
            second_arrival = self._parse_datetime(second_leg["arrival_time"])

            if not all(
                [first_departure, first_arrival, second_departure, second_arrival]
            ):
                return None

            total_transit_time = (
                first_leg["travel_time_minutes"]
                + transfer_info["transfer_walking_minutes"]
                + second_leg["travel_time_minutes"]
            )

            return {
                "route_path": [
                    {
                        "route_id": first_leg["route_id"],
                        "trip_id": first_leg["trip_id"],
                        "departure_time": first_leg["departure_time"],
                        "arrival_time": first_leg["arrival_time"],
                        "leg_type": "transit",
                    },
                    {
                        "transfer_station": transfer_info["name"],
                        "transfer_walking_minutes": transfer_info[
                            "transfer_walking_minutes"
                        ],
                        "leg_type": "transfer",
                    },
                    {
                        "route_id": second_leg["route_id"],
                        "trip_id": second_leg["trip_id"],
                        "departure_time": second_leg["departure_time"],
                        "arrival_time": second_leg["arrival_time"],
                        "leg_type": "transit",
                    },
                ],
                "final_stop": second_leg["final_stop"],
                "transit_time_minutes": total_transit_time,
                "num_transfers": 1,
                "arrival_time": second_leg["arrival_time"],
                "origin_walk_minutes": origin_walk_time,
                "dest_walk_minutes": second_leg["dest_walk_minutes"],
                "total_time_minutes": (
                    origin_walk_time
                    + total_transit_time
                    + second_leg["dest_walk_minutes"]
                ),
            }

        except Exception as e:
            logger.debug("Failed to combine route legs: %s", e)
            return None

    def _is_same_station(self, stop_id1: str, stop_id2: str) -> bool:
        """Check if two stop IDs refer to the same station (accounting for platforms)."""
        # Convert platform-specific IDs to parent station IDs for comparison
        parent1 = stop_id1 if stop_id1.startswith("place-") else stop_id1
        parent2 = stop_id2 if stop_id2.startswith("place-") else stop_id2

        return parent1 == parent2

    def _deduplicate_routes(self, routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate routes based on key characteristics."""
        seen_routes = set()
        unique_routes = []

        for route in routes:
            # Create a signature for deduplication
            route_signature = (
                route.get("num_transfers", 0),
                route.get("final_stop", {}).get("id", ""),
                route.get("total_time_minutes", 0) // 5,  # Group by 5-minute buckets
            )

            if route_signature not in seen_routes:
                seen_routes.add(route_signature)
                unique_routes.append(route)

        return unique_routes

    async def _graph_search_routes(
        self,
        origin_stop: dict[str, Any],
        dest_stops: list[dict[str, Any]],
        origin_departures: list[dict[str, Any]],
        departure_time: str | None,
        max_transfers: int,
        wheelchair_accessible: bool,
    ) -> list[dict[str, Any]]:
        """Use graph search to find routes from origin to destination stops."""
        # Constants
        max_initial_departures = 20
        max_routes_to_find = 10

        dest_stop_ids = {stop["id"] for stop in dest_stops}
        routes_found: list[dict[str, Any]] = []

        # Priority queue: (total_time, num_transfers, current_stop_id, route_path, arrival_time)
        pq: list[Any] = []

        # Initialize with departures from origin stop
        for departure in origin_departures[
            :max_initial_departures
        ]:  # Limit initial departures
            if wheelchair_accessible and not departure.get("attributes", {}).get(
                "wheelchair_accessible"
            ):
                continue

            departure_datetime = self._parse_datetime(
                departure.get("attributes", {}).get("departure_time")
                or departure.get("attributes", {}).get("arrival_time")
            )

            if not departure_datetime:
                continue

            # Check if this departure is after our desired departure time
            if departure_time:
                desired_dt = self._parse_datetime(departure_time)
                if desired_dt and departure_datetime < desired_dt:
                    continue

            heapq.heappush(
                pq,
                (
                    0,  # total_time so far
                    0,  # num_transfers
                    origin_stop["id"],
                    [
                        {
                            "stop": origin_stop,
                            "departure": departure,
                            "route_id": departure.get("relationships", {})
                            .get("route", {})
                            .get("data", {})
                            .get("id"),
                            "trip_id": departure.get("relationships", {})
                            .get("trip", {})
                            .get("data", {})
                            .get("id"),
                            "departure_time": departure_datetime.isoformat()
                            if departure_datetime
                            else None,
                        }
                    ],
                    departure_datetime,
                ),
            )

        visited = set()

        while pq and len(routes_found) < max_routes_to_find:  # Find up to 10 routes
            (
                current_time,
                num_transfers,
                current_stop_id,
                route_path,
                current_datetime,
            ) = heapq.heappop(pq)

            if (current_stop_id, num_transfers) in visited:
                continue
            visited.add((current_stop_id, num_transfers))

            # Check if we've reached a destination stop
            if current_stop_id in dest_stop_ids:
                final_stop = next(
                    stop for stop in dest_stops if stop["id"] == current_stop_id
                )
                routes_found.append(
                    {
                        "route_path": route_path,
                        "final_stop": final_stop,
                        "transit_time_minutes": current_time,
                        "num_transfers": num_transfers,
                        "arrival_time": current_datetime.isoformat()
                        if current_datetime
                        else None,
                    }
                )
                continue

            # Don't explore further if we've reached max transfers
            if num_transfers >= max_transfers:
                continue

            # Get current trip details to find next stops
            current_segment = route_path[-1]
            if current_segment["trip_id"]:
                try:
                    trip_details = await self.get_trip_details(
                        current_segment["trip_id"], include_schedule=True
                    )

                    if trip_details.get("included"):
                        await self._explore_trip_connections(
                            pq,
                            trip_details,
                            current_stop_id,
                            current_time,
                            num_transfers,
                            route_path,
                            current_datetime,
                            wheelchair_accessible,
                            visited,
                        )
                except Exception as e:
                    logger.debug(
                        "Failed to get trip details for %s: %s",
                        current_segment["trip_id"],
                        e,
                    )
                    continue

        return routes_found

    async def _explore_trip_connections(
        self,
        pq: list[Any],
        trip_details: dict[str, Any],
        current_stop_id: str,
        current_time: int,
        num_transfers: int,
        route_path: list[dict[str, Any]],
        current_datetime: datetime,
        wheelchair_accessible: bool,
        visited: set[tuple[str, int]],
    ) -> None:
        """Explore connections from current trip to other routes."""
        schedules = [
            item
            for item in trip_details.get("included", [])
            if item["type"] == "schedule"
        ]

        # Find current stop in schedule and explore subsequent stops
        current_found = False
        for schedule in schedules:
            stop_id = (
                schedule.get("relationships", {})
                .get("stop", {})
                .get("data", {})
                .get("id")
            )

            if stop_id == current_stop_id:
                current_found = True
                continue

            if current_found and stop_id:
                # This is a stop after our current position on this trip
                arrival_time_str = schedule.get("attributes", {}).get("arrival_time")
                if arrival_time_str:
                    arrival_datetime = self._parse_datetime(arrival_time_str)
                    if arrival_datetime and arrival_datetime > current_datetime:
                        travel_time = int(
                            (arrival_datetime - current_datetime).total_seconds() / 60
                        )

                        # Look for connections at this stop
                        try:
                            connections = await self.get_predictions_for_stop(
                                stop_id, page_limit=20
                            )
                            await self._add_transfer_options(
                                pq,
                                connections,
                                stop_id,
                                current_time + travel_time,
                                num_transfers + 1,
                                route_path,
                                arrival_datetime,
                                wheelchair_accessible,
                                visited,
                            )
                        except Exception as e:
                            logger.debug(
                                "Failed to get connections at stop %s: %s", stop_id, e
                            )

    async def _add_transfer_options(
        self,
        pq: list[Any],
        connections: dict[str, Any],
        stop_id: str,
        travel_time: int,
        num_transfers: int,
        route_path: list[dict[str, Any]],
        arrival_datetime: datetime,
        wheelchair_accessible: bool,
        visited: set[tuple[str, int]],
    ) -> None:
        """Add transfer options to the priority queue."""
        # Constants
        max_connections_limit = 10
        min_transfer_time_minutes = 5

        if not connections.get("data"):
            return

        current_route_id = route_path[-1]["route_id"]

        for connection in connections["data"][
            :max_connections_limit
        ]:  # Limit connections
            conn_route_id = (
                connection.get("relationships", {})
                .get("route", {})
                .get("data", {})
                .get("id")
            )

            # Skip same route (no transfer needed)
            if conn_route_id == current_route_id:
                continue

            if wheelchair_accessible and not connection.get("attributes", {}).get(
                "wheelchair_accessible"
            ):
                continue

            conn_departure_str = connection.get("attributes", {}).get("departure_time")
            if not conn_departure_str:
                continue

            conn_departure = self._parse_datetime(conn_departure_str)
            if not conn_departure or conn_departure <= arrival_datetime:
                continue

            # Add transfer time (5 minutes minimum)
            transfer_time = max(
                min_transfer_time_minutes,
                int((conn_departure - arrival_datetime).total_seconds() / 60),
            )

            if (stop_id, num_transfers) not in visited:
                new_route_path = [
                    *route_path,
                    {
                        "stop_id": stop_id,
                        "departure": connection,
                        "route_id": conn_route_id,
                        "trip_id": connection.get("relationships", {})
                        .get("trip", {})
                        .get("data", {})
                        .get("id"),
                        "departure_time": conn_departure.isoformat(),
                        "transfer_time_minutes": transfer_time,
                    },
                ]

                heapq.heappush(
                    pq,
                    (
                        travel_time + transfer_time,
                        num_transfers,
                        stop_id,
                        new_route_path,
                        conn_departure,
                    ),
                )

    def _calculate_walk_time(
        self,
        coords1: tuple[float, float],
        coords2: tuple[float, float],
        walk_speed_kmh: float = 5.0,
    ) -> int:
        """Calculate walking time in minutes between two coordinates."""
        distance_km = self._haversine_distance(
            coords1[0], coords1[1], coords2[0], coords2[1]
        )
        return max(1, int((distance_km / walk_speed_kmh) * 60))

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate the great circle distance between two points in kilometers."""
        earth_radius_km = 6371  # Earth's radius in kilometers

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return earth_radius_km * c

    @alru_cache(maxsize=1)
    async def _load_major_stations(self) -> dict[str, Any]:
        """Load major stations from static JSON file with caching."""
        try:
            data_path = Path(__file__).parent / "data" / "major_stations.json"
            with data_path.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load static station data: %s", e)
            return {"rapid_transit": [], "commuter_rail": []}

    async def _search_major_stations(
        self,
        query: str,
        latitude: float | None = None,
        longitude: float | None = None,
        radius: float | None = None,
        page_limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for stops in major stations data using fuzzy matching."""
        try:
            major_stations = await self._load_major_stations()
            all_stations = major_stations.get("rapid_transit", []) + major_stations.get("commuter_rail", [])
            
            # Convert stations to MBTA API format for consistent filtering
            api_format_stations = []
            for station in all_stations:
                api_station = {
                    "id": station["id"],
                    "type": "stop",
                    "attributes": {
                        "name": station["name"],
                        "latitude": station["latitude"],
                        "longitude": station["longitude"],
                        "municipality": station.get("municipality", ""),
                        "description": station.get("description", ""),
                        "location_type": station.get("location_type", 1),
                        "vehicle_type": station["route_type"],
                        "wheelchair_boarding": station.get("wheelchair_boarding", 1),
                    },
                    "_from_major_stations": True,
                }
                api_format_stations.append(api_station)
            
            # Apply location filtering if coordinates provided
            if latitude is not None and longitude is not None:
                radius_km = (radius or 1000) / 1000  # Convert to kilometers
                location_filtered = []
                
                for station in api_format_stations:
                    station_lat = station["attributes"]["latitude"]
                    station_lon = station["attributes"]["longitude"]
                    
                    distance_km = self._haversine_distance(
                        latitude, longitude, station_lat, station_lon
                    )
                    
                    if distance_km <= radius_km:
                        station["_distance_km"] = distance_km
                        location_filtered.append(station)
                
                api_format_stations = location_filtered
            
            # Apply fuzzy search if query provided
            if query:
                search_fields = ["attributes.name", "attributes.description", "id"]
                filtered_data = filter_data_fuzzy(
                    api_format_stations, query, search_fields, page_limit
                )
                return filtered_data
            
            # If no query, return all stations (up to limit)
            return api_format_stations[:page_limit]
            
        except Exception as e:
            logger.warning(f"Error searching major stations: {e}")
            return []

    async def _get_known_stations_near_coordinates(
        self,
        latitude: float,
        longitude: float,
        max_walk_distance: float,
    ) -> list[dict[str, Any]]:
        """Get known major stations near the given coordinates using static data."""
        try:
            major_stations = await self._load_major_stations()
            all_stations = major_stations.get("rapid_transit", []) + major_stations.get("commuter_rail", [])
            
            nearby_stations = []
            
            for station in all_stations:
                distance_km = self._haversine_distance(
                    latitude, longitude, station["latitude"], station["longitude"]
                )
                distance_m = distance_km * 1000
                
                if distance_m <= max_walk_distance:
                    # Convert to MBTA API format
                    stop_data = {
                        "id": station["id"],
                        "type": "stop",
                        "attributes": {
                            "name": station["name"],
                            "latitude": station["latitude"],
                            "longitude": station["longitude"],
                            "municipality": station.get("municipality", ""),
                            "description": station.get("description", ""),
                            "location_type": station.get("location_type", 1),
                            "vehicle_type": station["route_type"],
                            "wheelchair_boarding": station.get("wheelchair_boarding", 1),  # Assume accessible for major stations
                        },
                        "_distance_km": distance_km,
                        "_from_static_data": True,
                        "vehicle_type": station["route_type"],  # Add for compatibility
                        "wheelchair_boarding": station.get("wheelchair_boarding", 1),  # Add for compatibility
                    }
                    nearby_stations.append(stop_data)
            
            # Sort by distance
            nearby_stations.sort(key=lambda x: x["_distance_km"])
            
            return nearby_stations
            
        except Exception as e:
            logger.warning(f"Error getting known stations near coordinates: {e}")
            return []

    async def _find_nearby_transit_stops(
        self,
        latitude: float,
        longitude: float,
        max_walk_distance: float,
        max_stops_limit: int,
        wheelchair_accessible: bool = False,
    ) -> dict[str, Any]:
        """Find nearby transit stops with comprehensive search strategy.

        Uses multiple approaches to find the best transit options:
        1. Direct station lookup for known major stations
        2. Check static major stations data for reliable coordinates
        3. Geographic search for stops with coordinates
        4. Fuzzy search for major stations that may lack coordinates
        5. Prioritizes rapid transit over bus stops
        """
        rapid_transit_stops = []
        bus_stops = []

        # First, try direct station lookup for known major stations
        known_stations = await self._get_known_stations_near_coordinates(
            latitude, longitude, max_walk_distance
        )
        
        for station in known_stations:
            # Check wheelchair accessibility if required
            if wheelchair_accessible and not station.get("wheelchair_boarding", 0):
                continue
                
            if station.get("vehicle_type") in [0, 1, 2]:  # Light rail, subway, or commuter rail
                rapid_transit_stops.append(station)
            elif station.get("vehicle_type") == 3:  # Bus
                bus_stops.append(station)

        # If we found good coverage from direct lookup, use it
        if len(rapid_transit_stops) >= 2:
            logger.info(
                "Found %s nearby major stations from direct lookup",
                len(rapid_transit_stops),
            )
        else:
            # Fall back to static major stations data
            major_stations = await self._load_major_stations()
            all_major_stations = major_stations.get(
                "rapid_transit", []
            ) + major_stations.get("commuter_rail", [])

            # Find nearby major stations from static data
            for station in all_major_stations:
                distance_km = self._haversine_distance(
                    latitude, longitude, station["latitude"], station["longitude"]
                )
                distance_m = distance_km * 1000

                if distance_m <= max_walk_distance:
                    # Check wheelchair accessibility if required
                    if wheelchair_accessible and not station.get("wheelchair_boarding", 0):
                        continue
                        
                    # Convert to MBTA API format
                    stop_data = {
                        "id": station["id"],
                        "type": "stop",
                        "attributes": {
                            "name": station["name"],
                            "latitude": station["latitude"],
                            "longitude": station["longitude"],
                            "municipality": station.get("municipality", ""),
                            "description": station.get("description", ""),
                            "location_type": station.get("location_type", 1),
                            "vehicle_type": station["route_type"],
                            "wheelchair_boarding": station.get("wheelchair_boarding", 0),
                        },
                        "_distance_km": distance_km,
                        "_from_static_data": True,
                    }

                    if (
                        station["route_type"] in [0, 1] or station["route_type"] == 2
                    ):  # Light rail or subway
                        rapid_transit_stops.append(stop_data)

            # If still not enough, supplement with geographic API search
            if len(rapid_transit_stops) < 2:
                geographic_stops = await self.get_nearby_stops(
                    latitude, longitude, max_walk_distance * 2, max_stops_limit * 3
                )

                # Process geographically found stops
                existing_ids = {stop["id"] for stop in rapid_transit_stops}
                for stop in geographic_stops.get("data", []):
                    if stop["id"] in existing_ids:
                        continue

                    distance_m = stop.get("_distance_km", 0) * 1000
                    vehicle_type = stop["attributes"]["vehicle_type"]
                    
                    # Check wheelchair accessibility if required
                    if wheelchair_accessible:
                        wheelchair_boarding = stop["attributes"].get("wheelchair_boarding", 0)
                        if not wheelchair_boarding:
                            continue

                    if distance_m <= max_walk_distance:
                        if vehicle_type in [0, 1]:  # Light rail or subway
                            rapid_transit_stops.append(stop)
                        elif vehicle_type == 3:  # Bus
                            bus_stops.append(stop)

                # If still not enough rapid transit options, search by name patterns
                if len(rapid_transit_stops) < 2:
                    await self._supplement_with_station_search(
                        latitude, longitude, max_walk_distance, rapid_transit_stops
                    )

        # Sort by distance
        rapid_transit_stops.sort(key=lambda x: x.get("_distance_km", 0))
        bus_stops.sort(key=lambda x: x.get("_distance_km", 0))

        # Prefer rapid transit if available, otherwise use bus stops
        if rapid_transit_stops:
            result_data = rapid_transit_stops[:max_stops_limit]
            logger.info(
                f"Using {len(result_data)} rapid transit stops for trip planning"
            )
        else:
            result_data = bus_stops[:max_stops_limit]
            logger.info(f"Using {len(result_data)} bus stops for trip planning")

        return {"data": result_data, "jsonapi": {"version": "1.0"}, "links": {}}

    async def _supplement_with_station_search(
        self,
        latitude: float,
        longitude: float,
        max_walk_distance: float,
        existing_stops: list[dict[str, Any]],
    ) -> None:
        """Supplement geographic search with name-based searches for major stations."""
        existing_ids = {stop["id"] for stop in existing_stops}

        # Common search terms for areas that might have major stations
        search_terms = []

        # Determine likely area based on coordinates to search smarter
        if 42.35 <= latitude <= 42.37 and -71.09 <= longitude <= -71.08:
            search_terms.extend(["kendall", "mit", "central", "cambridge"])
        elif 42.34 <= latitude <= 42.36 and -71.08 <= longitude <= -71.06:
            search_terms.extend(["copley", "back bay", "boylston", "arlington"])
        elif 42.355 <= latitude <= 42.365 and -71.065 <= longitude <= -71.055:
            search_terms.extend(["downtown", "park", "state", "government"])

        # Always search for nearby major stations
        search_terms.extend(["station", "square"])

        for term in search_terms:
            try:
                search_results = await self.search_stops(term, page_limit=10)

                for stop in search_results.get("data", []):
                    # Skip if already found or if it's a bus stop
                    vehicle_type = stop["attributes"]["vehicle_type"]
                    if stop["id"] in existing_ids or vehicle_type not in [0, 1]:
                        continue

                    stop_lat = stop["attributes"]["latitude"]
                    stop_lon = stop["attributes"]["longitude"]

                    # If stop doesn't have coordinates, try parent station
                    if not stop_lat or not stop_lon:
                        parent_station = (
                            stop.get("relationships", {})
                            .get("parent_station", {})
                            .get("data")
                        )
                        if parent_station:
                            try:
                                parent_id = parent_station.get("id")
                                parent_result = await self._request(
                                    f"/stops/{parent_id}", {}
                                )
                                if parent_result.get("data"):
                                    parent_data = parent_result["data"]
                                    stop_lat = parent_data["attributes"]["latitude"]
                                    stop_lon = parent_data["attributes"]["longitude"]
                                    if stop_lat and stop_lon:
                                        stop["attributes"]["latitude"] = stop_lat
                                        stop["attributes"]["longitude"] = stop_lon
                                        stop["_from_parent"] = True
                            except Exception:
                                continue

                    if not stop_lat or not stop_lon:
                        continue

                    # Calculate distance
                    stop_lat = float(stop_lat)
                    stop_lon = float(stop_lon)
                    distance_km = self._haversine_distance(
                        latitude, longitude, stop_lat, stop_lon
                    )
                    distance_m = distance_km * 1000

                    # Add if within walking distance
                    if distance_m <= max_walk_distance:
                        stop["_distance_km"] = distance_km
                        existing_stops.append(stop)
                        existing_ids.add(stop["id"])

            except Exception as e:
                logger.debug("Failed to search for '%s': %s", term, e)
                continue

    def _parse_datetime(self, time_str: str | None) -> datetime | None:
        """Parse ISO datetime string to datetime object."""
        if not time_str:
            return None
        try:
            # Handle various datetime formats from MBTA API
            if "T" in time_str:
                dt = datetime.fromisoformat(time_str)
                # Ensure timezone-aware datetime
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
                return dt
            # Handle time-only format (HH:MM:SS)
            today = datetime.now().astimezone().date()
            # Parse time string manually to avoid naive datetime
            try:
                time_parts = time_str.split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                min_time_parts_for_seconds = 3
                second = (
                    int(time_parts[2])
                    if len(time_parts) >= min_time_parts_for_seconds
                    else 0
                )
                time_part = time(hour, minute, second)
            except (ValueError, IndexError):
                return None
            # Create timezone-aware datetime
            naive_dt = datetime.combine(today, time_part)
            return naive_dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
        except (ValueError, AttributeError):
            return None

    async def get_route_alternatives(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        primary_route_modes: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get alternative route options by excluding certain modes of transport.

        Args:
            origin_lat: Origin latitude
            origin_lon: Origin longitude
            dest_lat: Destination latitude
            dest_lon: Destination longitude
            primary_route_modes: List of route types to exclude from alternatives
                                (e.g., ['1'] to exclude subway routes)

        Returns:
            Dict containing alternative trip options
        """
        # Get all route options first
        all_routes = await self.plan_trip(origin_lat, origin_lon, dest_lat, dest_lon)

        if "error" in all_routes or not all_routes.get("trip_options"):
            return all_routes

        # Filter out routes that use excluded modes if specified
        if primary_route_modes:
            alternative_routes = []
            for route in all_routes["trip_options"]:
                route_uses_excluded = False
                for segment in route.get("route_path", []):
                    if segment.get("route_id"):
                        try:
                            route_details = await self.get_routes(
                                route_id=segment["route_id"]
                            )
                            if route_details.get("data"):
                                route_type = str(
                                    route_details["data"]["attributes"]["type"]
                                )
                                if route_type in primary_route_modes:
                                    route_uses_excluded = True
                                    break
                        except Exception as e:
                            logger.debug(
                                "Failed to get route details for %s: %s",
                                segment["route_id"],
                                e,
                            )
                            continue

                if not route_uses_excluded:
                    alternative_routes.append(route)

            all_routes["trip_options"] = alternative_routes[
                :5
            ]  # Keep top 5 alternatives

        return all_routes
