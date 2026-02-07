"""MCP (Model Context Protocol) support"""

import os
import json
import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

# Config paths
MCP_CONFIG_FILE = "/data/mcp_servers.json"
MCP_TOOLS_CACHE = "/data/mcp_tools_cache.json"


class MCPServer(BaseModel):
    """MCP Server configuration"""
    name: str
    url: str  # e.g. http://localhost:3001 or stdio://path/to/server
    enabled: bool = True
    transport: str = "http"  # http, stdio, sse
    api_key: Optional[str] = None
    description: Optional[str] = None


class MCPToolsCache:
    """Cache for tools loaded from MCP servers"""
    
    def __init__(self):
        self.tools: Dict[str, dict] = {}
        self.last_refresh: Optional[datetime] = None
        self.server_status: Dict[str, dict] = {}
    
    def load_cache(self):
        """Load cached tools from file"""
        if os.path.exists(MCP_TOOLS_CACHE):
            try:
                with open(MCP_TOOLS_CACHE) as f:
                    data = json.load(f)
                    self.tools = data.get("tools", {})
                    self.last_refresh = datetime.fromisoformat(data["last_refresh"]) if data.get("last_refresh") else None
                    self.server_status = data.get("server_status", {})
            except:
                pass
    
    def save_cache(self):
        """Save tools cache to file"""
        os.makedirs(os.path.dirname(MCP_TOOLS_CACHE), exist_ok=True)
        with open(MCP_TOOLS_CACHE, 'w') as f:
            json.dump({
                "tools": self.tools,
                "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
                "server_status": self.server_status
            }, f, indent=2)
    
    def add_tools(self, server_name: str, tools: List[dict]):
        """Add tools from an MCP server"""
        for tool in tools:
            tool_name = f"mcp_{server_name}_{tool['name']}"
            self.tools[tool_name] = {
                "name": tool_name,
                "original_name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", tool.get("parameters", {})),
                "source": f"mcp:{server_name}",
                "server": server_name,
                "enabled": True
            }
        self.last_refresh = datetime.now()
        self.save_cache()
    
    def clear_server_tools(self, server_name: str):
        """Remove all tools from a specific server"""
        to_remove = [name for name, tool in self.tools.items() if tool.get("server") == server_name]
        for name in to_remove:
            del self.tools[name]
        self.save_cache()


# Global MCP cache
mcp_cache = MCPToolsCache()


def load_mcp_config() -> Dict[str, MCPServer]:
    """Load MCP server configurations"""
    if os.path.exists(MCP_CONFIG_FILE):
        try:
            with open(MCP_CONFIG_FILE) as f:
                data = json.load(f)
                return {name: MCPServer(**server) for name, server in data.items()}
        except:
            pass
    return {}


def save_mcp_config(servers: Dict[str, MCPServer]):
    """Save MCP server configurations"""
    os.makedirs(os.path.dirname(MCP_CONFIG_FILE), exist_ok=True)
    with open(MCP_CONFIG_FILE, 'w') as f:
        json.dump({name: server.dict() for name, server in servers.items()}, f, indent=2)


async def fetch_mcp_tools(server: MCPServer) -> List[dict]:
    """Fetch tools from an MCP server"""
    if server.transport == "http":
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {}
                if server.api_key:
                    headers["Authorization"] = f"Bearer {server.api_key}"
                
                # MCP uses JSON-RPC 2.0
                response = await client.post(
                    f"{server.url}",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/list",
                        "params": {}
                    },
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data and "tools" in data["result"]:
                        return data["result"]["tools"]
                    # Fallback for non-standard MCP servers
                    if "tools" in data:
                        return data["tools"]
        except Exception as e:
            print(f"Error fetching tools from {server.name}: {e}")
    
    return []


async def call_mcp_tool(server: MCPServer, tool_name: str, arguments: dict) -> dict:
    """Call a tool on an MCP server"""
    if server.transport == "http":
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {}
                if server.api_key:
                    headers["Authorization"] = f"Bearer {server.api_key}"
                
                response = await client.post(
                    f"{server.url}",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    },
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        return {"success": True, "result": data["result"]}
                    if "error" in data:
                        return {"success": False, "error": data["error"]}
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return {"success": False, "error": f"Unsupported transport: {server.transport}"}
