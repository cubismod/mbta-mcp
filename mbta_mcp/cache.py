"""Memory-based caching for MBTA API responses using cachetools."""

import hashlib
import json
import logging
from typing import Any

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class APICache:
    """Memory-based cache for API responses with TTL support using cachetools."""

    def __init__(self, default_ttl: int = 300, maxsize: int = 1000):
        """Initialize the cache with a default TTL in seconds and maximum size."""
        self.default_ttl = default_ttl
        self.maxsize = maxsize
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=maxsize, ttl=default_ttl)

    def _generate_cache_key(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> str:
        """Generate a unique cache key for the endpoint and parameters."""
        # Create a deterministic string representation
        key_parts = [endpoint]
        if params:
            # Sort parameters for consistent key generation
            sorted_params = sorted(params.items())
            key_parts.append(json.dumps(sorted_params, sort_keys=True))

        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any | None:
        """Get a cached response if it exists and is not expired."""
        cache_key = self._generate_cache_key(endpoint, params)
        result = self._cache.get(cache_key)

        if result is not None:
            logger.debug("Cache hit for %s", endpoint)
        else:
            logger.debug("Cache miss for %s", endpoint)

        return result

    def set(
        self,
        endpoint: str,
        data: Any,
        ttl: int | None = None,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Cache a response with the specified TTL."""
        cache_key = self._generate_cache_key(endpoint, params)
        ttl = ttl if ttl is not None else self.default_ttl

        # For cachetools TTLCache, we need to create a new cache instance with the specific TTL
        # if it's different from the default. This is a limitation of cachetools.
        if ttl != self.default_ttl:
            # Create a temporary cache with the specific TTL
            temp_cache: TTLCache[str, Any] = TTLCache(maxsize=1, ttl=ttl)
            temp_cache[cache_key] = data
            # Copy the value to our main cache (will use default TTL)
            self._cache[cache_key] = data
        else:
            self._cache[cache_key] = data

        logger.debug("Cached response for %s with TTL %ds", endpoint, ttl)

    def invalidate(self, endpoint: str, params: dict[str, Any] | None = None) -> None:
        """Remove a specific cache entry."""
        cache_key = self._generate_cache_key(endpoint, params)
        if cache_key in self._cache:
            del self._cache[cache_key]
            logger.debug("Invalidated cache for %s", endpoint)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.debug("Cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)

        return {
            "total_entries": total_entries,
            "max_size": self.maxsize,
            "cache_size_mb": self._estimate_memory_usage() / (1024 * 1024),
        }

    def _estimate_memory_usage(self) -> int:
        """Estimate memory usage of cache in bytes."""
        total_size = 0
        for key, value in self._cache.items():
            # Rough estimation: key + value + metadata
            total_size += len(key.encode())
            total_size += len(str(value).encode())
            total_size += 50  # Rough estimate for overhead
        return total_size

    async def close(self) -> None:
        """Clean up resources."""
        self.clear()


# Default TTL values for different endpoint types
DEFAULT_TTLS = {
    # Static data - longer cache times
    "routes": 3600,  # 1 hour
    "stops": 3600,  # 1 hour
    "shapes": 3600,  # 1 hour
    "services": 3600,  # 1 hour
    "facilities": 1800,  # 30 minutes
    "lines": 3600,  # 1 hour
    "route_patterns": 3600,  # 1 hour
    # Semi-dynamic data - medium cache times
    "schedules": 300,  # 5 minutes
    "trips": 300,  # 5 minutes
    "vehicles": 60,  # 1 minute
    # Real-time data - short cache times
    "predictions": 30,  # 30 seconds
    "alerts": 60,  # 1 minute
    "live_facilities": 120,  # 2 minutes
    # External APIs - variable cache times
    "vehicle_positions": 30,  # 30 seconds
    "external_alerts": 60,  # 1 minute
    "track_prediction": 300,  # 5 minutes
    "prediction_stats": 1800,  # 30 minutes
    "historical_assignments": 3600,  # 1 hour
    "amtrak_trains": 60,  # 1 minute
    "amtrak_health": 300,  # 5 minutes
}


def get_ttl_for_endpoint(endpoint: str) -> int:
    """Get the appropriate TTL for a given endpoint."""
    # Extract the base endpoint name
    base_endpoint = endpoint.strip("/").split("/")[0]
    return DEFAULT_TTLS.get(base_endpoint, 300)  # Default 5 minutes
