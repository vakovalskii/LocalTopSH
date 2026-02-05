"""Send direct message to user"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
from config import CONFIG
from logger import tool_logger
from models import ToolResult, ToolContext


async def tool_send_dm(args: dict, ctx: ToolContext) -> ToolResult:
    """Send private message to a user"""
    user_id = args.get("user_id")
    text = args.get("text", "")
    
    if not user_id:
        return ToolResult(False, error="user_id required")
    
    if not text:
        return ToolResult(False, error="text required")
    
    # Security: only allow sending to the current user or explicit user_id
    # Don't allow spamming random users
    if user_id != ctx.user_id:
        tool_logger.warning(f"DM to other user blocked: {user_id}")
        return ToolResult(False, error="Can only send DM to yourself (security)")
    
    callback_url = CONFIG.userbot_url if ctx.source == "userbot" else CONFIG.bot_url
    
    tool_logger.info(f"Sending DM to {user_id}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{callback_url}/send_dm",
                json={
                    "user_id": user_id,
                    "text": text
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()
                if data.get("success"):
                    return ToolResult(True, output=f"✅ DM sent to {user_id}")
                return ToolResult(False, error=data.get("error", "Failed to send DM"))
    
    except Exception as e:
        tool_logger.error(f"Send DM error: {e}")
        return ToolResult(False, error=str(e))
