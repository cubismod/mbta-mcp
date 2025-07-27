# MBTA MCP Server

An MCP (Model Context Protocol) server for the MBTA V3 API, providing access to Boston's public transit data.

## Features

- **Routes**: Get information about MBTA routes (subway, bus, commuter rail, ferry)
- **Stops**: Find transit stops by location, route, or ID
- **Predictions**: Real-time arrival predictions
- **Schedules**: Scheduled service times
- **Trips**: Trip information and details
- **Alerts**: Service alerts and disruptions
- **Vehicles**: Real-time vehicle positions

## Installation

### Option 1: Install as a tool (Recommended)

Install directly with uv tool:

```bash
uv tool install mbta-mcp
```

Set your MBTA API key:

```bash
export MBTA_API_KEY=your_api_key_here
```

Run the server:

```bash
mbta-mcp
```

### Option 2: Development Setup

1. Clone and install dependencies:

   ```bash
   git clone https://github.com/cubismod/mbta-mcp.git
   cd mbta-mcp
   uv sync
   ```

2. Configure your MBTA API key:

   ```bash
   cp .env.example .env
   # Edit .env and add your MBTA_API_KEY
   ```

3. Get an API key from <https://api-v3.mbta.com>

## Usage

Run the MCP server:

```bash
# If installed as a tool
mbta-mcp

# If using development setup
uv run mbta-mcp
```

### Available Tools

**Core Transit Data:**

- `mbta_get_routes` - Get MBTA routes (subway, bus, commuter rail, ferry)
- `mbta_get_stops` - Get MBTA stops by ID, route, or location
- `mbta_get_predictions` - Get real-time arrival predictions
- `mbta_get_schedules` - Get scheduled service times
- `mbta_get_trips` - Get trip information and details
- `mbta_get_alerts` - Get service alerts and disruptions
- `mbta_get_vehicles` - Get real-time vehicle positions

**Extended Features:**

- `mbta_get_services` - Get service definitions and calendars
- `mbta_get_shapes` - Get route shape/path information for mapping
- `mbta_get_facilities` - Get facility information (elevators, escalators, parking)
- `mbta_get_live_facilities` - Get real-time facility status and outages
- `mbta_search_stops` - Search for stops by name or near a location
- `mbta_get_nearby_stops` - Get stops near a specific location
- `mbta_get_predictions_for_stop` - Get all predictions for a specific stop

## Integration with LLMs

### Claude Desktop

#### Option 1: Using uv tool (Recommended)

1. **Install the MCP server:**

   ```bash
   uv tool install mbta-mcp
   ```

2. **Add to Claude Desktop configuration:**

   On macOS, edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

   ```json
   {
     "mcpServers": {
       "mbta": {
         "command": "mbta-mcp",
         "env": {
           "MBTA_API_KEY": "your_api_key_here"
         }
       }
     }
   }
   ```

   On Windows, edit `%APPDATA%\Claude\claude_desktop_config.json` with the same content.

#### Option 2: Using development setup

1. **Clone and setup the MCP server:**

   ```bash
   git clone https://github.com/cubismod/mbta-mcp.git
   cd mbta-mcp
   task install-dev
   task verify  # Ensure everything works
   ```

2. **Configure your MBTA API key:**

   ```bash
   cp .env.example .env
   # Edit .env and add: MBTA_API_KEY=your_api_key_here
   ```

3. **Add to Claude Desktop configuration:**

   On macOS, edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

   ```json
   {
     "mcpServers": {
       "mbta": {
         "command": "uv",
         "args": ["run", "mbta-mcp"],
         "cwd": "/path/to/your/mbta-mcp",
         "env": {
           "MBTA_API_KEY": "your_api_key_here"
         }
       }
     }
   }
   ```

   On Windows, edit `%APPDATA%\Claude\claude_desktop_config.json` with the same content.

**Restart Claude Desktop** and you'll see "mbta" in the 🔌 icon, indicating the MCP server is connected.

### Other MCP-Compatible LLMs

#### Continue.dev

Using uv tool installation:

```json
{
  "mcpServers": [
    {
      "name": "mbta",
      "command": "mbta-mcp",
      "env": {
        "MBTA_API_KEY": "your_api_key_here"
      }
    }
  ]
}
```

Or with development setup:

```json
{
  "mcpServers": [
    {
      "name": "mbta",
      "command": "uv",
      "args": ["run", "mbta-mcp"],
      "cwd": "/path/to/your/mbta-mcp",
      "env": {
        "MBTA_API_KEY": "your_api_key_here"
      }
    }
  ]
}
```

#### Codeium

Using uv tool installation:

```json
{
  "mcp": {
    "servers": {
      "mbta": {
        "command": ["mbta-mcp"],
        "env": {
          "MBTA_API_KEY": "your_api_key_here"
        }
      }
    }
  }
}
```

Or with development setup:

```json
{
  "mcp": {
    "servers": {
      "mbta": {
        "command": ["uv", "run", "mbta-mcp"],
        "cwd": "/path/to/your/mbta-mcp",
        "env": {
          "MBTA_API_KEY": "your_api_key_here"
        }
      }
    }
  }
}
```

#### Generic MCP Client

**Using uv tool:**

- **Command:** `mbta-mcp`
- **Environment:** `MBTA_API_KEY=your_api_key_here`

**Using development setup:**

- **Command:** `uv run mbta-mcp`
- **Working Directory:** `/path/to/your/mbta-mcp`
- **Environment:** `MBTA_API_KEY=your_api_key_here`

### Usage Examples

Once connected, you can ask your LLM questions like:

- "What are the next Red Line trains from Harvard?"
- "Are there any service alerts for the Green Line?"
- "Find the nearest T stops to 42.3601° N, 71.0589° W"
- "What bus routes serve Kendall Square?"
- "Show me the schedule for Route 1 bus"

### Troubleshooting

**Server not connecting:**

1. Verify the path in your config is correct
2. Ensure `uv` is installed and in your PATH
3. Check that the MBTA API key is valid
4. Run `task test-server` to verify the server works

**API rate limiting:**

- The MBTA API has rate limits; the server includes pagination to manage this
- Some endpoints work without an API key, but having one increases limits

**Configuration issues:**

- Ensure your `.env` file is in the project root
- API key should be set as `MBTA_API_KEY=your_key_here`
- Check Claude Desktop logs if the server fails to start

## API Key Requirements

- **Free access:** Many endpoints work without an API key (with lower rate limits)
- **API key benefits:** Higher rate limits and access to all features
- **Get a key:** Register at <https://api-v3.mbta.com>
- **Usage:** Set in `.env` file or environment variable `MBTA_API_KEY`

## Development

This project uses [Task](https://taskfile.dev/) for build automation. Install it and run:

```bash
task --list  # Show available tasks
```

### Common Tasks

```bash
task install-dev    # Install dependencies including dev tools
task check          # Run all checks (format, lint, typecheck)
task test-server    # Test MCP server functionality
task run            # Run the MBTA MCP server
task verify         # Full project verification
```

### Manual Commands

Install dev dependencies:

```bash
uv sync --dev
```

Run formatters and linters:

```bash
task format     # or: uv run ruff format mbta_mcp/
task lint       # or: uv run ruff check mbta_mcp/
task typecheck  # or: uv run mypy mbta_mcp/
```

## Project Structure

```text
mbta-mcp/
├── mbta_mcp/
│   ├── __init__.py         # Package initialization
│   ├── client.py          # Core MBTA API client
│   ├── extended_client.py # Extended client with all endpoints
│   └── server.py          # MCP server implementation
├── .env.example           # Environment variables template
├── .tool-versions         # asdf tool versions (Python 3.13)
├── Taskfile.yml          # Build automation tasks
├── pyproject.toml        # Project configuration and dependencies
├── test_server.py        # Server functionality tests
└── README.md             # This file
```

**Key Files:**

- `mbta_mcp/server.py` - Main MCP server with 14 transit tools
- `mbta_mcp/client.py` - Async HTTP client for MBTA V3 API (using aiohttp)
- `Taskfile.yml` - Development commands and automation
- `.env.example` - Configuration template
