"""Configuration management for tools"""

import os
import json
from typing import Optional

# Config file path
CONFIG_FILE = "/data/tools_config.json"


def load_config() -> dict:
    """Load tool configuration (enabled/disabled state)"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(config: dict):
    """Save tool configuration"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def get_all_tools_with_state(
    shared_tools: dict,
    mcp_cache,
    skills_manager,
    user_id: Optional[str] = None
) -> dict:
    """Get all tools (builtin + MCP + Skills) with their enabled/disabled state"""
    config = load_config()
    tools = {}
    
    # Built-in tools
    for name, tool in shared_tools.items():
        enabled = config.get(name, {}).get("enabled", tool["enabled"])
        tools[name] = {
            **tool,
            "enabled": enabled
        }
    
    # MCP tools from cache
    mcp_cache.load_cache()
    for name, tool in mcp_cache.tools.items():
        enabled = config.get(name, {}).get("enabled", tool.get("enabled", True))
        tools[name] = {
            **tool,
            "enabled": enabled
        }
    
    # Skills tools (scan on each call for freshness)
    skills_manager.scan_all(user_id)
    for name, tool in skills_manager.get_enabled_tools().items():
        enabled = config.get(name, {}).get("enabled", tool.get("enabled", True))
        tools[name] = {
            **tool,
            "enabled": enabled
        }
    
    return tools
