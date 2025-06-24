#!/usr/bin/env python3
"""
Debug what the Rootly API is actually returning
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

async def debug_api_responses():
    """Debug what the API is actually returning."""
    config_path = Path(__file__).parent / "config" / "config.local-pip.json"
    with open(config_path) as f:
        config = json.load(f)
    
    client = RootlyMCPClient(config)
    
    try:
        async with client.connect() as session:
            print("✅ Connected to local MCP server")
            
            # Test users_get with raw response inspection
            print("\n🧪 Testing users_get (raw response):")
            try:
                result = await session.call_tool("users_get", {})
                print(f"Result type: {type(result)}")
                print(f"Has content: {hasattr(result, 'content')}")
                
                if result.content:
                    print(f"Content length: {len(result.content)}")
                    for i, content_item in enumerate(result.content):
                        print(f"Content[{i}] type: {type(content_item)}")
                        print(f"Content[{i}] text length: {len(content_item.text)}")
                        print(f"Content[{i}] raw text: '{content_item.text}'")
                        print(f"Content[{i}] first 200 chars: '{content_item.text[:200]}'")
                        
                        # Try to identify what type of response this is
                        text = content_item.text.strip()
                        if not text:
                            print("❌ Empty response!")
                        elif text.startswith('{'):
                            print("✅ Looks like JSON")
                            try:
                                data = json.loads(text)
                                print(f"✅ Valid JSON with keys: {list(data.keys())}")
                            except json.JSONDecodeError as e:
                                print(f"❌ Invalid JSON: {e}")
                        elif text.startswith('<'):
                            print("❌ Looks like HTML (probably error page)")
                        else:
                            print(f"❓ Unknown format, starts with: '{text[:50]}'")
                else:
                    print("❌ No content in response")
                    
            except Exception as e:
                print(f"❌ Error calling users_get: {e}")
                import traceback
                traceback.print_exc()
            
            # Test incidents_get
            print("\n🧪 Testing incidents_get (raw response):")
            try:
                result = await session.call_tool("incidents_get", {})
                if result.content:
                    for i, content_item in enumerate(result.content):
                        text = content_item.text.strip()
                        print(f"Incidents raw text: '{text[:200]}'")
                        if not text:
                            print("❌ Empty incidents response!")
                        elif text.startswith('{'):
                            try:
                                data = json.loads(text)
                                print(f"✅ Valid incidents JSON with keys: {list(data.keys())}")
                                if 'data' in data:
                                    print(f"Incidents data length: {len(data['data'])}")
                            except json.JSONDecodeError as e:
                                print(f"❌ Invalid incidents JSON: {e}")
                else:
                    print("❌ No content in incidents response")
                    
            except Exception as e:
                print(f"❌ Error calling incidents_get: {e}")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_api_responses())