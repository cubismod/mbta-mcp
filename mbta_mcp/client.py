"""MBTA V3 API client."""

import logging
import os
from typing import Any
from urllib.parse import urljoin

import aiohttp
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from .cache import APICache, get_ttl_for_endpoint

logger = logging.getLogger(__name__)


class MBTAClient:
    """Client for interacting with the MBTA V3 API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        enable_cache: bool = True,
    ):
        self.api_key = api_key or os.getenv("MBTA_API_KEY")
        self.base_url = base_url or os.getenv(
            "MBTA_BASE_URL", "https://api-v3.mbta.com"
        )
        self.session: aiohttp.ClientSession | None = None
        self.cache: APICache | None = APICache() if enable_cache else None

    async def __aenter__(self) -> "MBTAClient":
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if self.session:
            await self.session.close()
        if self.cache:
            await self.cache.close()

    def _get_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.api+json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    @retry(
        wait=wait_exponential_jitter(initial=1, max=60, jitter=2),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(
            (aiohttp.ClientError, aiohttp.ClientResponseError)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _request(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Make a request to the MBTA API with retry logic and caching."""
        if not self.base_url:
            raise ValueError("Base URL is required")
        if not self.session:
            raise RuntimeError(
                "Client session not initialized. Use 'async with' context."
            )

        # Check cache first
        if self.cache:
            cached_result = self.cache.get(endpoint, params)
            if cached_result is not None:
                return cached_result  # type: ignore[no-any-return]

        url = urljoin(self.base_url, endpoint)
        headers = self._get_headers()

        async with self.session.get(
            url, headers=headers, params=params or {}
        ) as response:
            response.raise_for_status()
            result: dict[str, Any] = await response.json()

            # Cache the result
            if self.cache:
                ttl = get_ttl_for_endpoint(endpoint)
                self.cache.set(endpoint, result, ttl, params)

            return result

    async def get_routes(
        self,
        route_id: str | None = None,
        route_type: int | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get routes from the MBTA API."""
        endpoint = f"/routes/{route_id}" if route_id else "/routes"
        params: dict[str, Any] = {"page[limit]": page_limit}
        if route_type is not None:
            params["filter[type]"] = route_type
        return await self._request(endpoint, params)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        if self.cache:
            return self.cache.get_stats()
        return {"error": "Cache not enabled"}

    def clear_cache(self) -> None:
        """Clear all cached responses."""
        if self.cache:
            self.cache.clear()

    def invalidate_cache(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> None:
        """Invalidate a specific cache entry."""
        if self.cache:
            self.cache.invalidate(endpoint, params)

    async def get_stops(
        self,
        stop_id: str | None = None,
        route_id: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        radius: float | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get stops from the MBTA API."""
        endpoint = f"/stops/{stop_id}" if stop_id else "/stops"
        params: dict[str, Any] = {"page[limit]": page_limit}

        if route_id:
            params["filter[route]"] = route_id
        if latitude is not None and longitude is not None:
            params["filter[latitude]"] = latitude
            params["filter[longitude]"] = longitude
            if radius is not None:
                params["filter[radius]"] = radius

        return await self._request(endpoint, params)

    async def get_predictions(
        self,
        stop_id: str | None = None,
        route_id: str | None = None,
        trip_id: str | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get predictions from the MBTA API."""
        params: dict[str, Any] = {"page[limit]": page_limit}

        if stop_id:
            params["filter[stop]"] = stop_id
        if route_id:
            params["filter[route]"] = route_id
        if trip_id:
            params["filter[trip]"] = trip_id

        return await self._request("/predictions", params)

    async def get_schedules(
        self,
        stop_id: str | None = None,
        route_id: str | None = None,
        trip_id: str | None = None,
        direction_id: int | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get schedules from the MBTA API."""
        params: dict[str, Any] = {"page[limit]": page_limit}

        if stop_id:
            params["filter[stop]"] = stop_id
        if route_id:
            params["filter[route]"] = route_id
        if trip_id:
            params["filter[trip]"] = trip_id
        if direction_id is not None:
            params["filter[direction_id]"] = direction_id

        return await self._request("/schedules", params)

    async def get_trips(
        self,
        trip_id: str | None = None,
        route_id: str | None = None,
        direction_id: int | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get trips from the MBTA API."""
        endpoint = f"/trips/{trip_id}" if trip_id else "/trips"
        params: dict[str, Any] = {"page[limit]": page_limit}

        if route_id:
            params["filter[route]"] = route_id
        if direction_id is not None:
            params["filter[direction_id]"] = direction_id

        return await self._request(endpoint, params)

    async def get_alerts(
        self,
        alert_id: str | None = None,
        route_id: str | None = None,
        stop_id: str | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get alerts from the MBTA API."""
        endpoint = f"/alerts/{alert_id}" if alert_id else "/alerts"
        params: dict[str, Any] = {"page[limit]": page_limit}

        if route_id:
            params["filter[route]"] = route_id
        if stop_id:
            params["filter[stop]"] = stop_id

        return await self._request(endpoint, params)

    async def get_vehicles(
        self,
        vehicle_id: str | None = None,
        route_id: str | None = None,
        trip_id: str | None = None,
        page_limit: int = 10,
    ) -> dict[str, Any]:
        """Get vehicles from the MBTA API."""
        endpoint = f"/vehicles/{vehicle_id}" if vehicle_id else "/vehicles"
        params: dict[str, Any] = {"page[limit]": page_limit}

        if route_id:
            params["filter[route]"] = route_id
        if trip_id:
            params["filter[trip]"] = trip_id

        return await self._request(endpoint, params)
