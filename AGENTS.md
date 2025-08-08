# Repository Guidelines

## Project Structure & Modules
- Source: `mbta_mcp/` (server, client, CLI, data). Entry points: `mbta_mcp.server:main` and `mbta_mcp.cli:main`.
- Tests: `tests/` plus some top-level `test_*.py`. Pytest discovers via `pyproject.toml`.
- Scripts: `scripts/` (e.g., data builders). Build artifacts in `dist/`.
- Config: `.env` (use `.env.example`), `pyproject.toml`, `Taskfile.yml`.

## Build, Test, and Dev Commands
- `task install`: Install runtime deps via `uv`.
- `task install-dev`: Install runtime + dev tools.
- `task run`: Run the MCP server (`uv run mbta-mcp`).
- `task test`: Run tests with pytest.
- `task format` / `task lint` / `task lint-fix`: Ruff format/lint.
- `task typecheck`: Mypy type checks.
- `task check` / `task dev`: Format+lint+types, or full dev setup.
- Example: `MBTA_API_KEY=... uv run mbta-mcp` or place key in `.env`.

## Coding Style & Naming
- Python 3.11+. Type hints required for new/changed functions.
- Formatting: Ruff `format` (double quotes, spaces, standard line length).
- Linting: Ruff with rules configured in `pyproject.toml`; fix with `task lint-fix`.
- Types: Mypy configured (strict on defs/incomplete defs). Prefer `pathlib`, `async` where applicable.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, module-level constants `UPPER_SNAKE`.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio` for async tests.
- Discovery: files named `test_*.py` in `tests/` or package roots.
- Conventions: Arrange–Act–Assert; mock external calls and env (`patch.dict(os.environ, {...})`).
- Run: `task test`. Keep tests deterministic; avoid real network I/O.

## Commit & PR Guidelines
- Commits: Clear, imperative subject (“Add trip planning schema validation”). Keep changes focused; include why when non-obvious.
- PRs: Describe intent, key changes, and testing. Link issues. Include run instructions if behavior changes.
- Quality gate: Ensure `task check` and `task test` pass; update README or in-code docs when adding tools/endpoints.

## Security & Configuration
- Secrets: Do not commit `.env` or keys. Use `MBTA_API_KEY` via environment or `.env`.
- Network usage may be rate-limited; design with retries/timeouts (see `tenacity`, `aiohttp`).

## Architecture Overview
- Server exposes MCP tools backed by `ExtendedMBTAClient` and `aiohttp`. CLI (`mbta-cli`) offers direct access for debugging. Keep new tools documented and validated via schemas.

