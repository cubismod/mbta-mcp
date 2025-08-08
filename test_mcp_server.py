#!/usr/bin/env python3
"""Test script to check MCP server functionality."""

import asyncio
import json
import subprocess
import sys
from typing import Any

async def test_mcp_server() -> None:
    """Test the MCP server functionality."""
    
    # Start the MCP server as a subprocess
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "mbta_mcp.server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        # Test initialization
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send initialization request
        await process.stdin.write((json.dumps(init_request) + "\n").encode())
        await process.stdin.drain()
        
        # Read response
        response = await process.stdout.readline()
        print(f"Init response: {response.decode().strip()}")
        
        # Test list tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        await process.stdin.write((json.dumps(list_tools_request) + "\n").encode())
        await process.stdin.drain()
        
        response = await process.stdout.readline()
        print(f"List tools response: {response.decode().strip()}")
        
        # Test trip planning
        trip_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "mbta_plan_trip",
                "arguments": {
                    "origin_lat": 42.39674,
                    "origin_lon": -71.121815,
                    "dest_lat": 42.352271,
                    "dest_lon": -71.055242,
                    "prefer_fewer_transfers": True
                }
            }
        }
        
        await process.stdin.write((json.dumps(trip_request) + "\n").encode())
        await process.stdin.drain()
        
        response = await process.stdout.readline()
        print(f"Trip planning response: {response.decode().strip()}")
        
    except Exception as e:
        print(f"Error testing MCP server: {e}")
    finally:
        # Clean up
        process.terminate()
        await process.wait()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
