#!/usr/bin/env python3
"""
Debug the tool schemas to see what parameters are required
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
    env_files = [".env", "secrets.env"]
    try:
        from dotenv import load_dotenv
        for env_file in env_files:
            env_path = Path(__file__).parent / env_file
            if env_path.exists():
                load_dotenv(env_path)
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

load_environment_variables()

from mcp_client import RootlyMCPClient

async def debug_tool_schemas():
    """Check the exact schemas for users_get and incidents_get tools."""
    config_path = Path(__file__).parent / "config" / "config.local-pip.json"
    with open(config_path) as f:
        config = json.load(f)
    
    client = RootlyMCPClient(config)
    
    try:
        async with client.connect() as session:
            print("✅ Connected to local MCP server")
            
            # Get all tools and their schemas
            tools_response = await session.list_tools()
            
            target_tools = ["users_get", "incidents_get"]
            
            for tool in tools_response.tools:
                if tool.name in target_tools:
                    print(f"\n🔧 Tool: {tool.name}")
                    print(f"Description: {tool.description}")
                    print(f"Input Schema: {json.dumps(tool.inputSchema, indent=2)}")
                    
                    # Try to figure out required parameters
                    if tool.inputSchema and 'properties' in tool.inputSchema:
                        props = tool.inputSchema['properties']
                        required = tool.inputSchema.get('required', [])
                        
                        print(f"Required parameters: {required}")
                        print("Available parameters:")
                        for prop_name, prop_info in props.items():
                            is_required = prop_name in required
                            prop_type = prop_info.get('type', 'unknown')
                            default = prop_info.get('default', 'no default')
                            desc = prop_info.get('description', 'no description')
                            print(f"  - {prop_name} ({prop_type}) {'[REQUIRED]' if is_required else '[OPTIONAL]'}")
                            print(f"    Default: {default}")
                            print(f"    Description: {desc}")
                    
                    print("-" * 50)
                    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_tool_schemas())