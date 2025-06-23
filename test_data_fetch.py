#!/usr/bin/env python3
"""
Test actual data fetching to see what's returned
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

# Set up auth header
if os.environ.get("ROOTLY_API_TOKEN"):
    os.environ["ROOTLY_AUTH_HEADER"] = f"Bearer {os.environ['ROOTLY_API_TOKEN']}"

from mcp_client import RootlyMCPClient

async def test_data_fetch():
    """Test actual data fetching."""
    config_path = Path(__file__).parent / "config" / "config.json"
    with open(config_path) as f:
        config = json.load(f)
    
    client = RootlyMCPClient(config)
    
    try:
        async with client.connect() as session:
            print("✅ Connected to MCP server")
            
            # Test users_get
            print("\n🧪 Testing users_get:")
            try:
                result = await session.call_tool("users_get", {})
                if result.content:
                    data = json.loads(result.content[0].text)
                    print(f"Raw response: {json.dumps(data, indent=2)}")
                    print(f"Type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
                        if 'data' in data:
                            users = data['data']
                            print(f"Users count: {len(users)}")
                            if users:
                                print(f"Sample user keys: {list(users[0].keys())}")
            except Exception as e:
                print(f"Error: {e}")
            
            # Test incidents_get  
            print("\n🧪 Testing incidents_get:")
            try:
                result = await session.call_tool("incidents_get", {})
                if result.content:
                    data = json.loads(result.content[0].text)
                    print(f"Raw response: {json.dumps(data, indent=2)}")
                    print(f"Type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
                        if 'data' in data:
                            incidents = data['data'] 
                            print(f"Incidents count: {len(incidents)}")
                            if incidents:
                                print(f"Sample incident keys: {list(incidents[0].keys())}")
            except Exception as e:
                print(f"Error: {e}")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_data_fetch())