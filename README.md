# MBTA MCP Server

![PyPI - Version](https://img.shields.io/pypi/v/mbta-mcp?link=https%3A%2F%2Fpypi.org%2Fproject%2Fmbta-mcp%2F)

An MCP (Model Context Protocol) server for the MBTA V3 API, providing access to Boston's public transit data.

## Features

- **Routes**: Get information about MBTA routes (subway, bus, commuter rail, ferry)
- **Stops**: Find transit stops by location, route, or ID
- **Predictions**: Real-time arrival predictions
- **Schedules**: Scheduled service times
- **Trips**: Trip information and details
- **Alerts**: Service alerts and disruptions
- **Vehicles**: Real-time vehicle positions
- **Trip Planning**: Intelligent multi-modal journey planning with real-time data
- **Route Alternatives**: Alternative routing options with transfer optimization
- **External APIs**: Vehicle positions and alerts from external sources
- **Track Predictions**: Machine learning-powered track assignment predictions
- **Historical Data**: Access to historical track assignments and performance metrics
- **Caching**: Memory-based caching with configurable TTL for improved performance
- **Resource Data**: Static reference data including route types, transit hubs, fare information, service hours, and trip planning prompts

## Installation

### Option 1: Direct run with uv (Easiest)

No installation required! Just run directly:

```bash
uv tool run mbta-mcp
```

Set your MBTA API key as an environment variable:

```bash
export MBTA_API_KEY=your_api_key_here
uv tool run mbta-mcp
```

### Option 2: Install as a tool

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

### Option 3: Development Setup

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

### MCP Server (for AI clients)

Run the MCP server for use with AI clients like Claude Desktop:

```bash
# Direct run (no installation needed)
uv tool run mbta-mcp

# If installed as a tool
mbta-mcp

# If using development setup
uv run mbta-mcp
```

### CLI Interface (for direct usage)

For direct command-line access to MBTA and Amtrak data:

```bash
# Show available commands
uv run mbta-cli --help

# Get Amtrak trains
uv run mbta-cli trains --limit 5

# Get Amtrak trains in JSON format
uv run mbta-cli trains --json --limit 3

# Test MBTA routes
uv run mbta-cli routes

# Show available MCP tools
uv run mbta-cli tools
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

**Trip Planning:**

- `mbta_plan_trip` - Plan multi-modal journeys with real-time data and transfer optimization
- `mbta_get_route_alternatives` - Find alternative routes with different transit modes

**Extended Features:**

- `mbta_get_services` - Get service definitions and calendars
- `mbta_get_shapes` - Get route shape/path information for mapping
- `mbta_get_facilities` - Get facility information (elevators, escalators, parking)
- `mbta_get_live_facilities` - Get real-time facility status and outages
- `mbta_search_stops` - Search for stops by name or near a location
- `mbta_get_nearby_stops` - Get stops near a specific location
- `mbta_get_predictions_for_stop` - Get all predictions for a specific stop

**External API Tools:**

- `mbta_get_vehicle_positions` - Get real-time vehicle positions from external API (GeoJSON format)
- `mbta_get_external_alerts` - Get general alerts from external API (delays, disruptions, service info)

**Boston Amtrak Tracker API:**

- `mbta_get_amtrak_trains` - Get all tracked Amtrak trains from Boston Amtrak Tracker API
- `mbta_get_amtrak_trains_geojson` - Get Amtrak trains as GeoJSON for mapping applications
- `mbta_get_amtrak_health_status` - Get health status of the Boston Amtrak Tracker API

**IMT Track Prediction API:**

- `mbta_get_track_prediction` - Predict which track a train will use at a station
- `mbta_get_chained_track_predictions` - Get multiple track predictions in a single request
- `mbta_get_prediction_stats` - Get prediction statistics and accuracy metrics
- `mbta_get_historical_assignments` - Get historical track assignments for analysis

## Tool Reference

### Core Transit Data Tools

#### `mbta_get_routes`

Get information about MBTA routes including subway, bus, commuter rail, and ferry services.

- **Parameters:** `route_id` (optional), `route_type` (optional), `page_limit` (default: 10)
- **Route Types:** 0=Light Rail, 1=Subway, 2=Commuter Rail, 3=Bus, 4=Ferry

#### `mbta_get_stops`

Find transit stops by location, route, or ID with optional filtering.

- **Parameters:** `stop_id` (optional), `route_id` (optional), `latitude`/`longitude` (optional), `radius` (optional), `page_limit` (default: 10)

#### `mbta_get_predictions`

Get real-time arrival predictions for MBTA services.

- **Parameters:** `stop_id` (optional), `route_id` (optional), `trip_id` (optional), `page_limit` (default: 10)

#### `mbta_get_schedules`

Get scheduled service times and departure information.

- **Parameters:** `stop_id` (optional), `route_id` (optional), `trip_id` (optional), `direction_id` (optional), `page_limit` (default: 10)

#### `mbta_get_trips`

Get trip information and details for MBTA services.

- **Parameters:** `trip_id` (optional), `route_id` (optional), `direction_id` (optional), `page_limit` (default: 10)

#### `mbta_get_alerts`

Get service alerts and disruptions affecting MBTA services.

- **Parameters:** `alert_id` (optional), `route_id` (optional), `stop_id` (optional), `page_limit` (default: 10)

#### `mbta_get_vehicles`

Get real-time vehicle positions and status information.

- **Parameters:** `vehicle_id` (optional), `route_id` (optional), `trip_id` (optional), `page_limit` (default: 10)

### Extended Features Tools

#### `mbta_get_services`

Get service definitions and calendars for MBTA operations.

- **Parameters:** `service_id` (optional), `page_limit` (default: 10)

#### `mbta_get_shapes`

Get route shape/path information for mapping and visualization.

- **Parameters:** `shape_id` (optional), `route_id` (optional), `page_limit` (default: 10)

#### `mbta_get_facilities`

Get facility information including elevators, escalators, and parking areas.

- **Parameters:** `facility_id` (optional), `stop_id` (optional), `facility_type` (optional), `page_limit` (default: 10)

#### `mbta_get_live_facilities`

Get real-time facility status and outage information.

- **Parameters:** `facility_id` (optional), `page_limit` (default: 10)

#### `mbta_search_stops`

Search for stops by name or near a specific location.

- **Parameters:** `query` (required), `latitude`/`longitude` (optional), `radius` (optional), `page_limit` (default: 10)

#### `mbta_get_nearby_stops`

Get stops near a specific location within a specified radius.

- **Parameters:** `latitude` (required), `longitude` (required), `radius` (default: 1000), `page_limit` (default: 10)

#### `mbta_get_predictions_for_stop`

Get all predictions for a specific stop with optional filtering.

- **Parameters:** `stop_id` (required), `route_id` (optional), `direction_id` (optional), `page_limit` (default: 10)

### External API Tools

#### `mbta_get_vehicle_positions`

Get real-time vehicle positions from external API in GeoJSON format.

- **Parameters:** None
- **Returns:** GeoJSON with vehicle locations, routes, status, speed, and bearing information

#### `mbta_get_external_alerts`

Get general alerts from external API including delays, disruptions, and service information.

- **Parameters:** None
- **Returns:** JSON with alert details, severity levels, affected routes/stops, and active periods

### Boston Amtrak Tracker API Tools

#### `mbta_get_amtrak_trains`

Get all tracked Amtrak trains from the Boston Amtrak Tracker API.

- **Parameters:** None
- **Returns:** JSON with real-time Amtrak train locations, routes, status, speed, and other information

#### `mbta_get_amtrak_trains_geojson`

Get Amtrak trains as GeoJSON for mapping applications.

- **Parameters:** None
- **Returns:** GeoJSON feature collection with train locations suitable for mapping

#### `mbta_get_amtrak_health_status`

Get health status of the Boston Amtrak Tracker API.

- **Parameters:** None
- **Returns:** JSON with server health status and last data update time

### IMT Track Prediction API Tools

#### `mbta_get_track_prediction`

Predict which track a train will use at a specific station using machine learning.

- **Parameters:** `station_id` (required), `route_id` (required), `trip_id` (required), `headsign` (required), `direction_id` (required), `scheduled_time` (required)
- **Returns:** Track prediction with confidence score and prediction method

#### `mbta_get_chained_track_predictions`

Get multiple track predictions in a single request for batch processing.

- **Parameters:** `predictions` (required) - Array of prediction request objects
- **Returns:** Array of track predictions with confidence scores

#### `mbta_get_prediction_stats`

Get prediction statistics and accuracy metrics for a station and route.

- **Parameters:** `station_id` (required), `route_id` (required)
- **Returns:** Statistics including accuracy rate, total predictions, correct predictions, and average confidence

#### `mbta_get_historical_assignments`

Get historical track assignments for analysis and pattern recognition.

- **Parameters:** `station_id` (required), `route_id` (required), `days` (default: 30)
- **Returns:** Historical track assignment data with actual usage patterns

### Resource Data

The MBTA MCP server provides access to static reference data that can be used for trip planning, fare calculations, and general transit information. These resources are available through the MCP resources protocol.

#### Available Resources

- **Route Types** (`mbta://data/route_types.json`): Complete information about MBTA route types including subway, bus, commuter rail, and ferry services with descriptions, examples, and visual identifiers.

- **Transit Hubs** (`mbta://data/transit_hubs.json`): Information about major transit hubs and transfer points in the MBTA system, including South Station, North Station, Back Bay, and other key locations.

- **Fare Information** (`mbta://data/fare_information.json`): Complete MBTA fare structure including subway, bus, commuter rail, and ferry pricing, payment methods, and discount information.

- **Service Hours** (`mbta://data/service_hours.json`): MBTA service hours and frequency information for all transit modes, including peak hours and special services.

- **Major Stations** (`mbta://data/major_stations.json`): Comprehensive database of major MBTA stations with location and service information.

- **Trip Planning Prompts** (`mbta://data/trip_planning_prompts.json`): Comprehensive collection of trip planning prompts for common scenarios including airport transfers, daily commutes, event planning, accessibility needs, and emergency situations.

#### Using Resources

Resources can be accessed through MCP-compatible clients that support the resources protocol. The data is provided in JSON format and includes structured information for programmatic use.

**Example Resource Usage:**
- Access route type information for UI development
- Get fare information for cost calculations
- Use transit hub data for transfer planning
- Reference service hours for scheduling
- Apply trip planning prompts for common scenarios

### Trip Planning Tools

The MBTA MCP server provides intelligent trip planning capabilities that combine real-time transit data with multi-modal journey optimization. These tools help plan efficient journeys across the MBTA network with support for accessibility requirements and transfer preferences.

#### `mbta_plan_trip`

Plan multi-modal journeys with real-time data and transfer optimization. This tool finds the best transit routes between two locations, considering walking distance, transfer limits, and accessibility requirements.

**Parameters:**
- `origin_lat` (required): Origin latitude coordinate
- `origin_lon` (required): Origin longitude coordinate  
- `dest_lat` (required): Destination latitude coordinate
- `dest_lon` (required): Destination longitude coordinate
- `departure_time` (optional): ISO 8601 formatted departure time (e.g., "2025-01-01T10:00:00-05:00")
- `max_walk_distance` (optional): Maximum walking distance in meters (default: 800)
- `max_transfers` (optional): Maximum number of transfers allowed (default: 2)
- `prefer_fewer_transfers` (optional): Prioritize routes with fewer transfers (default: true)
- `wheelchair_accessible` (optional): Only include accessible routes and vehicles (default: false)

**Returns:** JSON with trip options including:
- Origin and destination coordinates with nearby transit stops
- Multiple route alternatives with detailed segments
- Walking directions and transit connections
- Real-time departure predictions and schedule information
- Transfer points and walking times between stations
- Accessibility information for each route option

**Example Usage:**
```
Plan a trip from MIT to Harvard Square:
- origin_lat: 42.3601
- origin_lon: -71.0942  
- dest_lat: 42.3736
- dest_lon: -71.1190
- max_walk_distance: 600
- prefer_fewer_transfers: true
```

#### `mbta_get_route_alternatives`

Find alternative routes with different transit modes. This tool excludes specified primary route types to discover backup options, useful when primary routes have service disruptions.

**Parameters:**
- `origin_lat` (required): Origin latitude coordinate
- `origin_lon` (required): Origin longitude coordinate
- `dest_lat` (required): Destination latitude coordinate  
- `dest_lon` (required): Destination longitude coordinate
- `primary_route_modes` (optional): Array of route type IDs to exclude (e.g., ["1"] to exclude subway)
- `departure_time` (optional): ISO 8601 formatted departure time
- `max_walk_distance` (optional): Maximum walking distance in meters (default: 800)
- `max_transfers` (optional): Maximum transfers (default: 2)
- `wheelchair_accessible` (optional): Require accessible routes (default: false)

**Route Type IDs:**
- `"0"` - Light Rail (Green Line branches)
- `"1"` - Subway (Red, Orange, Blue Lines)  
- `"2"` - Commuter Rail
- `"3"` - Bus
- `"4"` - Ferry

**Returns:** Alternative route options excluding the specified primary modes, with the same detailed structure as `mbta_plan_trip`.

**Example Usage:**
```
Find bus alternatives when subway is disrupted:
- origin_lat: 42.3601
- origin_lon: -71.0942
- dest_lat: 42.3736  
- dest_lon: -71.1190
- primary_route_modes: ["1", "0"]  // Exclude subway and light rail
- max_walk_distance: 1000
```

### Trip Planning Use Cases

**Morning Commute Planning:**
Use `mbta_plan_trip` with departure time to find the best route for your daily commute, considering real-time delays and service alerts.

**Accessibility-First Routing:**
Enable `wheelchair_accessible: true` to ensure all suggested routes are fully accessible, including elevators and ramps at stations.

**Service Disruption Backup:**
When alerts indicate subway delays, use `mbta_get_route_alternatives` to find bus routes that avoid the affected lines.

**Event Planning:**
For large events, plan trips with longer walking distances and more transfers to distribute passenger load across the transit network.

**Tourist Assistance:**
Combine trip planning with nearby stops and predictions to help visitors navigate Boston's transit system efficiently.

## Integration with LLMs

### Claude Desktop

#### Option 1: Using uv tool run (Easiest - No Installation Required)

**Add to Claude Desktop configuration:**

On macOS, edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mbta": {
      "command": "uv",
      "args": ["tool", "run", "mbta-mcp"],
      "env": {
        "MBTA_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

On Windows, edit `%APPDATA%\Claude\claude_desktop_config.json` with the same content.

#### Option 2: Using uv tool install (Recommended for Regular Use)

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

#### Option 3: Using development setup

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

**Using uv tool run (easiest):**

```json
{
  "mcpServers": [
    {
      "name": "mbta",
      "command": "uv",
      "args": ["tool", "run", "mbta-mcp"],
      "env": {
        "MBTA_API_KEY": "your_api_key_here"
      }
    }
  ]
}
```

**Using uv tool installation:**

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

**Or with development setup:**

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

**Using uv tool run (easiest):**

```json
{
  "mcp": {
    "servers": {
      "mbta": {
        "command": ["uv", "tool", "run", "mbta-mcp"],
        "env": {
          "MBTA_API_KEY": "your_api_key_here"
        }
      }
    }
  }
}
```

**Using uv tool installation:**

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

**Or with development setup:**

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

**Using uv tool run (easiest):**

- **Command:** `uv tool run mbta-mcp`
- **Environment:** `MBTA_API_KEY=your_api_key_here`

**Using uv tool install:**

- **Command:** `mbta-mcp`
- **Environment:** `MBTA_API_KEY=your_api_key_here`

**Using development setup:**

- **Command:** `uv run mbta-mcp`
- **Working Directory:** `/path/to/your/mbta-mcp`
- **Environment:** `MBTA_API_KEY=your_api_key_here`

### Usage Examples

Once connected, you can ask your LLM questions like:

**Core Transit Information:**
- "What are the next Red Line trains from Harvard?"
- "Are there any service alerts for the Green Line?"
- "Find the nearest T stops to 42.3601° N, 71.0589° W"
- "What bus routes serve Kendall Square?"
- "Show me the schedule for Route 1 bus"
- "Get real-time vehicle positions for all MBTA vehicles"
- "What are the current service alerts and delays?"

**Trip Planning:**
- "Plan a trip from MIT (42.3601, -71.0942) to Harvard Square (42.3736, -71.1190)"
- "How do I get from Back Bay to Logan Airport using only accessible routes?"
- "Find alternative routes from Downtown Crossing to Fenway that avoid the Green Line"
- "Plan a wheelchair-accessible journey from South Station to Cambridge with minimal walking"
- "What's the best way to get from Kendall Square to Copley at 8:30 AM tomorrow?"
- "Show me bus alternatives from Harvard to MIT when the Red Line is down"
- "Plan a trip allowing up to 1200 meters of walking and 3 transfers maximum"

**Advanced Features:**
- "Predict which track the 3:30 PM Providence train will use at South Station"
- "Show me track prediction accuracy statistics for South Station"
- "Get historical track assignments for the last 30 days"
- "Get all current Amtrak trains in the Boston area"
- "Show me Amtrak trains as GeoJSON for mapping"
- "Check the health status of the Amtrak tracker API"

**Resource Data:**
- "Show me the MBTA route types and their descriptions"
- "What are the major transit hubs in Boston?"
- "Get the current fare information for subway and bus"
- "What are the service hours for the Red Line?"
- "Show me trip planning prompts for airport transfers"
- "Get accessibility information for major stations"

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

## External APIs

This MCP server integrates with additional external APIs to provide enhanced functionality:

### Vehicle Positions API

- **Endpoint:** <https://vehicles.ryanwallace.cloud/>
- **Format:** GeoJSON with real-time vehicle locations, routes, and status
- **No authentication required**
- **Data:** Vehicle coordinates, route information, speed, bearing, occupancy status

### External Alerts API

- **Endpoint:** <https://vehicles.ryanwallace.cloud/alerts>
- **Format:** JSON with service alerts, delays, and disruptions
- **No authentication required**
- **Data:** Alert headers, effects, severity levels, affected routes/stops, active periods

### IMT Track Prediction API

- **Endpoint:** <https://imt.ryanwallace.cloud/>
- **Format:** JSON with machine learning-powered track predictions
- **No authentication required**
- **Data:** Track predictions, confidence scores, historical assignments, accuracy metrics

### Boston Amtrak Tracker API

- **Endpoint:** <https://bos.ryanwallace.cloud/>
- **Format:** JSON and GeoJSON with real-time Amtrak train tracking
- **No authentication required**
- **Data:** Train locations, routes, status, speed, and health information


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
