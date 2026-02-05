"""Message management: edit/delete"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
from config import CONFIG
from logger import tool_logger
from models import ToolResult, ToolContext


async def tool_manage_message(args: dict, ctx: ToolContext) -> ToolResult:
    """Edit or delete bot messages"""
    action = args.get("action", "")
    message_id = args.get("message_id")
    text = args.get("text", "")
    
    if not action:
        return ToolResult(False, error="Action required: edit or delete")
    
    if not message_id:
        return ToolResult(False, error="message_id required")
    
    callback_url = CONFIG.userbot_url if ctx.source == "userbot" else CONFIG.bot_url
    
    try:
        async with aiohttp.ClientSession() as session:
            if action == "edit":
                if not text:
                    return ToolResult(False, error="text required for edit")
                
                tool_logger.info(f"Editing message {message_id}")
                async with session.post(
                    f"{callback_url}/edit",
                    json={
                        "chat_id": ctx.chat_id,
                        "message_id": message_id,
                        "text": text
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json()
                    if data.get("success"):
                        return ToolResult(True, output=f"✅ Message {message_id} edited")
                    return ToolResult(False, error=data.get("error", "Edit failed"))
            
            elif action == "delete":
                tool_logger.info(f"Deleting message {message_id}")
                async with session.post(
                    f"{callback_url}/delete",
                    json={
                        "chat_id": ctx.chat_id,
                        "message_id": message_id
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    data = await resp.json()
                    if data.get("success"):
                        return ToolResult(True, output=f"✅ Message {message_id} deleted")
                    return ToolResult(False, error=data.get("error", "Delete failed"))
            
            else:
                return ToolResult(False, error=f"Unknown action: {action}. Use 'edit' or 'delete'")
    
    except Exception as e:
        tool_logger.error(f"Message action error: {e}")
        return ToolResult(False, error=str(e))
