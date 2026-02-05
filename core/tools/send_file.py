"""Send file to chat"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import aiohttp
from config import CONFIG
from logger import tool_logger
from models import ToolResult, ToolContext
from tools.files import normalize_path


async def tool_send_file(args: dict, ctx: ToolContext) -> ToolResult:
    """Send file from workspace to chat"""
    path = args.get("path", "")
    caption = args.get("caption", "")
    
    tool_logger.info(f"[send_file] Called with path={path}, cwd={ctx.cwd}")
    
    if not path:
        return ToolResult(False, error="Path required")
    
    # Normalize path
    original_path = path
    path = normalize_path(path, ctx.cwd)
    tool_logger.info(f"[send_file] Normalized: {original_path} -> {path}")
    
    # Check file exists (with retry for race condition / sync delay)
    for attempt in range(5):
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        tool_logger.info(f"[send_file] Attempt {attempt+1}/5: exists={exists}, size={size}")
        
        if exists and size > 0:
            break
        await asyncio.sleep(2)
    
    if not os.path.exists(path):
        # List dir to debug
        dir_path = os.path.dirname(path)
        try:
            files = os.listdir(dir_path) if os.path.isdir(dir_path) else []
            tool_logger.warning(f"[send_file] Dir {dir_path} contents: {files[:10]}")
        except Exception as e:
            tool_logger.warning(f"[send_file] Can't list dir: {e}")
        return ToolResult(False, error=f"File not found: {path}")
    
    # Check file size
    file_size = os.path.getsize(path)
    if file_size > 50 * 1024 * 1024:
        return ToolResult(False, error="File too large (max 50MB)")
    
    tool_logger.info(f"Sending file: {path}")
    
    # Determine callback URL based on source
    callback_url = CONFIG.userbot_url if ctx.source == "userbot" else CONFIG.bot_url
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{callback_url}/send_file",
                json={
                    "chat_id": ctx.chat_id,
                    "file_path": path,
                    "caption": caption
                },
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                data = await resp.json()
                if data.get("success"):
                    tool_logger.info(f"File sent: {path}")
                    return ToolResult(True, output=f"✅ File sent: {os.path.basename(path)}")
                else:
                    return ToolResult(False, error=data.get("error", "Failed to send"))
    except Exception as e:
        tool_logger.error(f"Send file error: {e}")
        return ToolResult(False, error=str(e))
