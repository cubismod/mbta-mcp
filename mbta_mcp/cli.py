"""CLI interface for MBTA MCP server."""

import asyncio
import json

import click

from .extended_client import ExtendedMBTAClient


async def show_available_tools() -> None:
    """Show available MBTA tools."""
    click.echo("🚇 MBTA MCP Server - Available Tools")
    click.echo("=" * 50)

    tools = [
        ("mbta_get_routes", "Get MBTA routes (subway, bus, commuter rail, ferry)"),
        ("mbta_get_stops", "Find transit stops by location, route, or ID"),
        ("mbta_get_predictions", "Real-time arrival predictions"),
        ("mbta_get_schedules", "Scheduled service times"),
        ("mbta_get_trips", "Trip information and details"),
        ("mbta_get_alerts", "Service alerts and disruptions"),
        ("mbta_get_vehicles", "Real-time vehicle positions"),
        ("mbta_get_amtrak_trains", "Get Amtrak trains from Boston Amtrak Tracker"),
        ("mbta_get_vehicle_positions", "External vehicle positions API"),
        ("mbta_get_external_alerts", "External alerts API"),
    ]

    for i, (tool, description) in enumerate(tools, 1):
        click.echo(f"{i:2d}. {tool}")
        click.echo(f"    {description}")
        click.echo()

    click.echo("💡 This tool is designed to run as an MCP server.")
    click.echo("   For direct usage, try: uv run python test_server.py")
    click.echo("   For Amtrak trains: uv run python test_amtrak.py")


async def test_amtrak_trains() -> None:
    """Test Amtrak trains functionality."""
    click.echo("🚂 Testing Amtrak trains...")

    async with ExtendedMBTAClient() as client:
        try:
            trains = await client.get_amtrak_trains()
            click.echo(f"✓ Found {len(trains)} Amtrak trains")

            if trains:
                click.echo("\n📍 Sample trains:")
                for i, train in enumerate(trains[:3], 1):
                    if isinstance(train, dict):
                        click.echo(
                            f"{i}. {train.get('route', 'Unknown')} - {train.get('stop', 'Unknown')}"
                        )
                        click.echo(f"   Speed: {train.get('speed', 'Unknown')} mph")
                        click.echo(
                            f"   Status: {train.get('current_status', 'Unknown')}"
                        )
                        click.echo()

        except (ValueError, RuntimeError, ConnectionError) as e:
            click.echo(f"❌ Error: {e}", err=True)


async def test_mbta_routes() -> None:
    """Test MBTA routes functionality."""
    click.echo("🚇 Testing MBTA routes...")

    async with ExtendedMBTAClient() as client:
        try:
            routes = await client.get_routes(page_limit=5)
            data = routes.get("data", [])
            click.echo(f"✓ Found {len(data)} MBTA routes")

            if data:
                click.echo("\n📍 Sample routes:")
                for i, route in enumerate(data[:3], 1):
                    attrs = route.get("attributes", {})
                    click.echo(f"{i}. {attrs.get('long_name', 'Unknown')}")
                    click.echo(f"   Type: {attrs.get('type', 'Unknown')}")
                    click.echo(f"   ID: {route.get('id', 'Unknown')}")
                    click.echo()

        except (ValueError, RuntimeError, ConnectionError) as e:
            click.echo(f"❌ Error: {e}", err=True)


@click.group()
@click.version_option()
def cli() -> None:
    """MBTA MCP Server CLI - Access Boston transit data and Amtrak trains."""


@cli.command()
def tools() -> None:
    """Show available MBTA MCP tools."""
    asyncio.run(show_available_tools())


@cli.command()
def amtrak() -> None:
    """Test Amtrak trains functionality."""
    asyncio.run(test_amtrak_trains())


@cli.command()
def routes() -> None:
    """Test MBTA routes functionality."""
    asyncio.run(test_mbta_routes())


@cli.command()
@click.option("--limit", "-l", default=10, help="Number of trains to show")
@click.option("--json", "output_json", is_flag=True, help="Output in JSON format")
def trains(limit: int, output_json: bool) -> None:
    """Get Amtrak trains with optional filtering."""

    async def get_trains() -> None:
        async with ExtendedMBTAClient() as client:
            try:
                trains = await client.get_amtrak_trains()
                if output_json:
                    click.echo(json.dumps(trains[:limit], indent=2))
                else:
                    click.echo(f"🚂 Found {len(trains)} Amtrak trains")
                    for i, train in enumerate(trains[:limit], 1):
                        if isinstance(train, dict):
                            click.echo(f"\n{i}. Train ID: {train.get('id', 'Unknown')}")
                            click.echo(f"   Route: {train.get('route', 'Unknown')}")
                            click.echo(
                                f"   Status: {train.get('current_status', 'Unknown')}"
                            )
                            click.echo(
                                f"   Location: {train.get('latitude', 'Unknown')}, {train.get('longitude', 'Unknown')}"
                            )
                            click.echo(f"   Speed: {train.get('speed', 'Unknown')} mph")
                            click.echo(f"   Stop: {train.get('stop', 'Unknown')}")
                            click.echo(
                                f"   Headsign: {train.get('headsign', 'Unknown')}"
                            )
            except (ValueError, RuntimeError, ConnectionError) as e:
                click.echo(f"❌ Error: {e}", err=True)

    asyncio.run(get_trains())


def main() -> None:
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
