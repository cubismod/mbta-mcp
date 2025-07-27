#!/usr/bin/env python3
"""Simple test script to verify the MCP server starts up correctly."""

import asyncio
import sys


async def test_server_startup():
    """Test that the server can start up and list tools."""
    try:
        # Import the handler functions directly
        from mbta_mcp.server import handle_list_tools, handle_call_tool
        
        # Test tool listing
        tools = await handle_list_tools()
        print(f"✓ Server has {len(tools)} tools available:")
        for tool in tools[:3]:  # Show first 3 tools
            print(f"  - {tool.name}: {tool.description}")
        if len(tools) > 3:
            print(f"  ... and {len(tools) - 3} more")
        
        # Test a simple tool call (this will fail without API key, but should not crash)
        try:
            result = await handle_call_tool("mbta_get_routes", {"page_limit": 1})
            print(f"✓ Tool call succeeded: {len(result[0].text)} characters returned")
            # Check if it's an error message
            if "Error:" in result[0].text:
                print("✓ Tool call properly returns error for missing API key")
            else:
                print("✓ Tool call succeeded (API key may be configured)")
        except Exception as e:
            print(f"✗ Unexpected error in tool call: {e}")
            return False
        
        print("✓ MCP server startup test passed!")
        return True
        
    except Exception as e:
        print(f"✗ Server startup test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_server_startup())
    sys.exit(0 if success else 1)