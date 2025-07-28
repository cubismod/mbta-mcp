# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is an MCP (Model Context Protocol) server that provides LLMs with access to Boston's MBTA V3 API. The architecture follows a layered approach:

**Core Components:**

- `mbta_mcp/client.py`: Base HTTP client using aiohttp with async session management
- `mbta_mcp/extended_client.py`: Extends base client with all 14 MBTA API endpoints
- `mbta_mcp/server.py`: MCP server implementation with tool registration and dispatch

**MCP Integration Pattern:**
The server registers 14 tools that map to MBTA API endpoints. Each tool is defined with JSON schemas for input validation and calls the appropriate client method. The server uses async context managers for proper resource cleanup.

**API Client Architecture:**

- Uses aiohttp.ClientSession for HTTP requests with proper async lifecycle
- Base client handles authentication headers and error handling
- Extended client adds endpoint-specific methods with parameter validation
- Both clients require `async with` context for session management

## Development Commands

**Primary workflow using Task:**

```bash
task verify          # Full verification (install, check, test)
task install-dev     # Install all dependencies including dev tools
task check           # Run format, lint, and typecheck
task test-server     # Test MCP server functionality
task run             # Start the MCP server
```

**Individual quality checks:**

```bash
task format          # Format code with ruff
task lint            # Lint with ruff (30+ rule categories)
task lint-fix        # Auto-fix linting issues
task typecheck       # Type check with strict mypy
```

**Direct uv commands:**

```bash
uv sync --dev        # Install dependencies
uv run mbta-mcp      # Run the server directly
uv run mypy mbta_mcp/
uv run ruff check mbta_mcp/
uv run ruff format mbta_mcp/
```

## Configuration & Setup

**Environment setup:**

- Copy `.env.example` to `.env` and add `MBTA_API_KEY`
- MBTA API key is optional (some endpoints work without it)
- Uses Python 3.11+ with asdf version management

**Project uses modern Python tooling:**

- Dynamic versioning from git tags via hatch-vcs
- uv for dependency management
- ruff for both linting and formatting (replaces black)
- Comprehensive type checking with mypy strict mode

## MCP Server Integration

**Adding new tools:**

1. Add endpoint method to `ExtendedMBTAClient`
2. Register tool in `handle_list_tools()` with JSON schema
3. Add handler case in `handle_call_tool()`

**Tool naming convention:** All tools prefixed with `mbta_` followed by action (e.g., `mbta_get_routes`, `mbta_search_stops`)

**Error handling:** Client exceptions are caught and returned as MCP TextContent with error messages

## Testing & Verification

**Server testing:**

- `test_server.py` validates server startup and tool functionality
- Tests tool registration, API calls, and error handling
- Run via `task test-server` or `uv run python test_server.py`

**Quality gates:**

- All code must pass ruff linting (30+ rule categories)
- Strict mypy type checking with no errors
- Format with ruff (double quotes, 88 char lines)

## Dependencies

**Runtime:** aiohttp (async HTTP), mcp (Model Context Protocol), pydantic (validation), python-dotenv (config)

**Development:** mypy, ruff, pytest, pytest-asyncio, codespell, hatch-vcs

**Version management:** Dynamic versioning from git using hatch-vcs, auto-generates `_version.py`

## API Swagger/OpenAPI Specs

- The MBTA API is defined at <https://api-v3.mbta.com/docs/swagger/swagger.json>
- The IMT API is defined at <https://imt.ryanwallace.cloud/openapi.json>
- The BOS Amtrak API is defined at <https://bos.ryanwallace.cloud/openapi.json>
