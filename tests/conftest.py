"""Pytest configuration and fixtures for MBTA MCP tests."""

from collections.abc import Generator
from types import TracebackType
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from .fixtures import MockMBTAResponse, get_mock_response_for_url


@pytest.fixture
def mock_aiohttp_session() -> Generator[AsyncMock, None, None]:
    """Mock aiohttp ClientSession for MBTA API calls."""

    async def mock_get(
        url: str, params: dict[str, Any] | None = None, **_kwargs: Any
    ) -> MockMBTAResponse:
        """Mock GET request."""
        return get_mock_response_for_url(url, params)

    async def mock_post(
        url: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        **_kwargs: Any,
    ) -> MockMBTAResponse:
        """Mock POST request."""
        return get_mock_response_for_url(url, params or json)

    with patch("aiohttp.ClientSession") as mock_session_class:
        mock_session = AsyncMock()
        mock_session.get = mock_get
        mock_session.post = mock_post
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None
        mock_session_class.return_value = mock_session
        yield mock_session


@pytest.fixture
def mock_mbta_client() -> Generator[Any, None, None]:
    """Mock MBTA client that uses mocked session."""

    async def create_mock_session() -> AsyncMock:
        """Create a mock session context manager."""
        mock_session = AsyncMock()

        # Mock HTTP methods to return appropriate responses
        async def mock_get(
            url: str, params: dict[str, Any] | None = None, **_kwargs: Any
        ) -> MockMBTAResponse:
            return get_mock_response_for_url(url, params)

        async def mock_post(
            url: str,
            params: dict[str, Any] | None = None,
            json: dict[str, Any] | None = None,
            **_kwargs: Any,
        ) -> MockMBTAResponse:
            return get_mock_response_for_url(url, params or json)

        mock_session.get = mock_get
        mock_session.post = mock_post
        return mock_session

    # Patch the client session creation
    with patch("mbta_mcp.client.aiohttp.ClientSession") as mock_session_class:
        mock_session_class.side_effect = create_mock_session
        yield mock_session_class


@pytest.fixture(autouse=True)
def mock_api_globally() -> Generator[None, None, None]:
    """Automatically mock MBTA API for all tests to prevent real API calls."""

    def create_mock_session(**_kwargs: Any) -> AsyncMock:
        mock_session = AsyncMock()

        # Create mock context manager methods
        async def mock_aenter() -> AsyncMock:
            return mock_session

        async def mock_aexit(
            exc_type: type[BaseException] | None,  # noqa: ARG001
            exc_val: BaseException | None,  # noqa: ARG001
            exc_tb: TracebackType | None,  # noqa: ARG001
        ) -> None:
            return None

        async def mock_close() -> None:
            return None

        # Mock HTTP methods to return context managers
        def mock_get(
            url: str, params: dict[str, Any] | None = None, **_request_kwargs: Any
        ) -> MockMBTAResponse:
            mock_response = get_mock_response_for_url(url, params)

            # Create a mock context manager
            async def mock_aenter() -> MockMBTAResponse:
                return mock_response

            async def mock_aexit(
                exc_type: type[BaseException] | None,  # noqa: ARG001
                exc_val: BaseException | None,  # noqa: ARG001
                exc_tb: TracebackType | None,  # noqa: ARG001
            ) -> None:
                return None

            mock_response.__aenter__ = mock_aenter  # type: ignore[method-assign]
            mock_response.__aexit__ = mock_aexit  # type: ignore[method-assign]
            return mock_response

        def mock_post(
            url: str,
            params: dict[str, Any] | None = None,
            json: dict[str, Any] | None = None,
            **_request_kwargs: Any,
        ) -> MockMBTAResponse:
            mock_response = get_mock_response_for_url(url, params or json)

            # Create a mock context manager
            async def mock_aenter() -> MockMBTAResponse:
                return mock_response

            async def mock_aexit(
                exc_type: type[BaseException] | None,  # noqa: ARG001
                exc_val: BaseException | None,  # noqa: ARG001
                exc_tb: TracebackType | None,  # noqa: ARG001
            ) -> None:
                return None

            mock_response.__aenter__ = mock_aenter  # type: ignore[method-assign]
            mock_response.__aexit__ = mock_aexit  # type: ignore[method-assign]
            return mock_response

        # Set up the mock session
        mock_session.__aenter__ = mock_aenter
        mock_session.__aexit__ = mock_aexit
        mock_session.close = mock_close
        mock_session.get = mock_get
        mock_session.post = mock_post

        return mock_session

    with patch("aiohttp.ClientSession", side_effect=create_mock_session):
        yield


@pytest.fixture
def sample_coordinates() -> dict[str, dict[str, float]]:
    """Sample coordinates for testing."""
    return {
        "mit": {"lat": 42.3601, "lon": -71.0942},
        "harvard": {"lat": 42.3736, "lon": -71.1190},
        "park_street": {"lat": 42.35639457, "lon": -71.0624242},
        "nyc": {"lat": 40.7128, "lon": -74.0060},  # Remote location
    }


@pytest.fixture
def trip_planning_params() -> dict[str, Any]:
    """Common trip planning parameters."""
    return {
        "origin_lat": 42.3601,
        "origin_lon": -71.0942,
        "dest_lat": 42.3736,
        "dest_lon": -71.1190,
        "max_walk_distance": 800,
        "max_transfers": 2,
        "prefer_fewer_transfers": True,
        "wheelchair_accessible": False,
    }
