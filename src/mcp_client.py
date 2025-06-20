"""
MCP Client for connecting to Rootly MCP server.
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class RootlyMCPClient:
    """Client for interacting with Rootly MCP server."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session: Optional[ClientSession] = None
        self.server_params = self._create_server_params()
        
    def _create_server_params(self) -> StdioServerParameters:
        """Create server parameters for MCP connection."""
        mcp_config = self.config.get("mcp_server", {})
        
        # Resolve environment variables in command args
        args = []
        for arg in mcp_config.get("args", []):
            if arg.startswith("${") and arg.endswith("}"):
                env_var = arg[2:-1]
                args.append(os.getenv(env_var, arg))
            else:
                args.append(arg)
        
        return StdioServerParameters(
            command=mcp_config.get("command", "python"),
            args=args,
            env=self._resolve_env_vars(mcp_config.get("env", {}))
        )
    
    def _resolve_env_vars(self, env_dict: Dict[str, str]) -> Dict[str, str]:
        """Resolve environment variable placeholders."""
        resolved = {}
        for key, value in env_dict.items():
            if value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                resolved[key] = os.getenv(env_var, value)
            else:
                resolved[key] = value
        return resolved
    
    @asynccontextmanager
    async def connect(self):
        """Context manager for MCP server connection."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                
                # Initialize the session
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                logger.info(f"Connected to Rootly MCP server with {len(tools.tools)} tools available")
                
                yield session
    
    async def get_users(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch all users from Rootly."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            result = await self.session.call_tool("users_get", {})
            if result.content:
                data = json.loads(result.content[0].text)
                return data.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return []
    
    async def get_incidents(
        self, 
        days_back: int = 30, 
        per_page: int = 100,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """Fetch incidents from the last N days."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            # Use the incidents_get tool without parameters (returns all)
            result = await self.session.call_tool("incidents_get", {})
            if result.content:
                data = json.loads(result.content[0].text)
                return data.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Error fetching incidents: {e}")
            return []
    
    async def get_all_incidents(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Fetch all incidents with pagination."""
        all_incidents = []
        page = 1
        per_page = 100
        
        while True:
            incidents = await self.get_incidents(days_back, per_page, page)
            if not incidents:
                break
            
            all_incidents.extend(incidents)
            
            # If we got less than per_page, we're on the last page
            if len(incidents) < per_page:
                break
            
            page += 1
            
        logger.info(f"Fetched {len(all_incidents)} incidents from last {days_back} days")
        return all_incidents
    
    async def get_incident_details(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific incident."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            result = await self.session.call_tool(
                "get_incident", 
                {"incident_id": incident_id, "include": "events,roles,action_items"}
            )
            if result.content:
                data = json.loads(result.content[0].text)
                return data.get("data", {})
            return None
        except Exception as e:
            logger.error(f"Error fetching incident {incident_id}: {e}")
            return None
    


async def test_connection(config: Dict[str, Any]) -> bool:
    """Test MCP server connection."""
    try:
        client = RootlyMCPClient(config)
        async with client.connect() as session:
            tools = await session.list_tools()
            print(f"Connected successfully. Available tools: {len(tools.tools)}")
            return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test the MCP client
    import json
    
    # Load config
    config_path = "../config/config.example.json"
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = json.load(f)
    else:
        config = {
            "mcp_server": {
                "command": "python",
                "args": ["-m", "rootly_mcp_server"],
                "env": {"ROOTLY_API_TOKEN": "${ROOTLY_API_TOKEN}"}
            }
        }
    
    # Test connection
    asyncio.run(test_connection(config))