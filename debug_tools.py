#!/usr/bin/env python3
"""
Debug script to list available MCP tools.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, try manual loading
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_client import RootlyMCPClient


async def debug_tools():
    """List all available tools and try some calls."""
    config_path = "config/config.json"
    with open(config_path) as f:
        config = json.load(f)
    
    client = RootlyMCPClient(config)
    
    async with client.connect() as session:
        # List all tools
        tools = await session.list_tools()
        print("Available tools:")
        for tool in tools.tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Try calling a specific tool
        print("\nTrying to call users_get...")
        try:
            result = await session.call_tool("users_get", {})
            print(f"Success! Result: {result.content[0].text[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\nTrying to call incidents_get...")
        try:
            result = await session.call_tool("incidents_get", {})
            print(f"Success! Result: {result.content[0].text[:200]}...")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(debug_tools())