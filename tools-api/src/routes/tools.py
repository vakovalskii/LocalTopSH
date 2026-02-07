"""Tools API routes"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..tools import SHARED_TOOLS, BOT_ONLY_TOOLS
from ..mcp import mcp_cache
from ..skills import skills_manager
from ..config import load_config, save_config, get_all_tools_with_state

router = APIRouter(tags=["tools"])


@router.get("/tools")
async def get_all_tools(user_id: Optional[str] = None):
    """Get all tools with their definitions and state"""
    tools = get_all_tools_with_state(SHARED_TOOLS, mcp_cache, skills_manager, user_id)
    
    builtin_count = len([t for t in tools.values() if t.get("source") == "builtin"])
    mcp_count = len([t for t in tools.values() if t.get("source", "").startswith("mcp:")])
    skill_count = len([t for t in tools.values() if t.get("source", "").startswith("skill:")])
    
    return {
        "tools": list(tools.values()),
        "bot_only_tools": BOT_ONLY_TOOLS,
        "stats": {
            "builtin": builtin_count,
            "mcp": mcp_count,
            "skill": skill_count,
            "total": len(tools)
        }
    }


@router.get("/tools/enabled")
async def get_enabled_tools(user_id: Optional[str] = None):
    """Get only enabled tools in OpenAI format (for agent)
    
    Pass user_id to include user-specific skills from their workspace.
    Tools are refreshed on each call to pick up new skills.
    """
    tools = get_all_tools_with_state(SHARED_TOOLS, mcp_cache, skills_manager, user_id)
    enabled = []
    
    for tool in tools.values():
        if tool["enabled"]:
            enabled.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
    
    return {"tools": enabled, "count": len(enabled)}


@router.get("/tools/search")
async def search_tools(query: str = "", source: str = "all"):
    """Search tools by name or description"""
    tools = get_all_tools_with_state(SHARED_TOOLS, mcp_cache, skills_manager, None)
    results = []
    
    query_lower = query.lower()
    
    for tool in tools.values():
        # Filter by source
        if source != "all":
            tool_source = tool.get("source", "builtin")
            if source == "builtin" and tool_source != "builtin":
                continue
            if source == "mcp" and not tool_source.startswith("mcp:"):
                continue
            if source == "skill" and not tool_source.startswith("skill:"):
                continue
        
        # Match query
        if not query or query_lower in tool["name"].lower() or query_lower in tool.get("description", "").lower():
            results.append(tool)
    
    return {"tools": results, "count": len(results)}


@router.get("/tools/{name}")
async def get_tool(name: str):
    """Get specific tool definition"""
    tools = get_all_tools_with_state(SHARED_TOOLS, mcp_cache, skills_manager, None)
    if name in tools:
        return tools[name]
    raise HTTPException(404, f"Tool {name} not found")


class ToolToggle(BaseModel):
    enabled: bool


@router.put("/tools/{name}")
async def toggle_tool(name: str, data: ToolToggle):
    """Enable or disable a tool"""
    tools = get_all_tools_with_state(SHARED_TOOLS, mcp_cache, skills_manager, None)
    
    if name not in tools:
        raise HTTPException(404, f"Tool {name} not found")
    
    config = load_config()
    if name not in config:
        config[name] = {}
    config[name]["enabled"] = data.enabled
    save_config(config)
    
    return {"success": True, "name": name, "enabled": data.enabled}


@router.delete("/tools/{name}")
async def reset_tool(name: str):
    """Reset tool to default state"""
    config = load_config()
    
    if name in config:
        del config[name]
        save_config(config)
    
    return {"success": True, "name": name, "message": "Reset to default"}
