#!/usr/bin/env python3
"""
Debug script to check available MCP tools and their schemas
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment
def load_environment_variables():
    """Load environment variables from multiple sources."""
    env_files = [".env", "secrets.env"]
    
    try:
        from dotenv import load_dotenv
        for env_file in env_files:
            env_path = Path(__file__).parent / env_file
            if env_path.exists():
                load_dotenv(env_path)
                print(f"Loaded environment from {env_file}")
    except ImportError:
        for env_file in env_files:
            env_path = Path(__file__).parent / env_file
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                value = value.strip('"\'')
                                os.environ[key] = value
                print(f"Loaded environment from {env_file}")

load_environment_variables()

# Set up auth header
if os.environ.get("ROOTLY_API_TOKEN"):
    os.environ["ROOTLY_AUTH_HEADER"] = f"Bearer {os.environ['ROOTLY_API_TOKEN']}"
    print("✓ Rootly authentication configured")

from mcp_client import RootlyMCPClient

async def debug_mcp_tools():
    """Debug MCP server tools and capabilities."""
    print("=" * 50)
    print("MCP SERVER DEBUGGING")
    print("=" * 50)
    
    # Load config
    config_path = Path(__file__).parent / "config" / "config.json"
    with open(config_path) as f:
        config = json.load(f)
    
    client = RootlyMCPClient(config)
    
    try:
        async with client.connect() as session:
            print("✅ Connected to MCP server")
            
            # List all available tools
            tools_response = await session.list_tools()
            print(f"\n📋 Available Tools ({len(tools_response.tools)}):")
            print("-" * 30)
            
            for tool in tools_response.tools:
                print(f"🔧 {tool.name}")
                print(f"   Description: {tool.description}")
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    print(f"   Input Schema: {tool.inputSchema}")
                print()
            
            # Test specific tool calls that might work
            print("\n🧪 Testing Tool Calls:")
            print("-" * 30)
            
            # Try different tool names that might exist
            tool_names_to_try = [
                "users_get", "get_users", "list_users", "users",
                "incidents_get", "get_incidents", "list_incidents", "incidents",
                "users_list", "incidents_list"
            ]
            
            available_tool_names = [tool.name for tool in tools_response.tools]
            
            for tool_name in tool_names_to_try:
                if tool_name in available_tool_names:
                    print(f"🎯 Testing {tool_name}...")
                    try:
                        result = await session.call_tool(tool_name, {})
                        if result.content:
                            data = json.loads(result.content[0].text)
                            if isinstance(data, dict) and 'data' in data:
                                items = data['data']
                                print(f"   ✅ Success: {len(items)} items returned")
                                if items:
                                    print(f"   📝 Sample item keys: {list(items[0].keys())}")
                            else:
                                print(f"   ✅ Success: {len(str(data))} chars returned")
                        else:
                            print(f"   ⚠️  No content returned")
                    except Exception as e:
                        print(f"   ❌ Error: {str(e)}")
                    print()
            
            # Show first few available tool names for reference
            print(f"\n📝 All Available Tool Names:")
            for i, name in enumerate(available_tool_names):
                print(f"   {i+1:2d}. {name}")
                if i >= 20:  # Limit output
                    print(f"   ... and {len(available_tool_names) - 21} more")
                    break
                    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_mcp_tools())