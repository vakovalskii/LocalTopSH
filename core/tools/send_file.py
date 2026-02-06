"""Send file to chat

Security: Core reads file and sends bytes to bot via multipart.
Bot does NOT have access to workspace volume.
"""

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
    
    # Normalize path (ensures user can only access their workspace)
    original_path = path
    path = normalize_path(path, ctx.cwd)
    tool_logger.info(f"[send_file] Normalized: {original_path} -> {path}")
    
    # Security: verify path is within user's workspace
    user_workspace = f"/workspace/{ctx.user_id}"
    if not path.startswith(user_workspace):
        tool_logger.warning(f"[send_file] Security: attempt to access outside workspace: {path}")
        return ToolResult(False, error="Access denied: file outside your workspace")
    
    # Check file exists (with retry for race condition / sync delay)
    for attempt in range(5):
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        tool_logger.info(f"[send_file] Attempt {attempt+1}/5: exists={exists}, size={size}")
        
        if exists and size > 0:
            break
        await asyncio.sleep(2)
    
    if not os.path.exists(path):
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
    
    tool_logger.info(f"Sending file: {path} ({file_size} bytes)")
    
    # Determine callback URL based on source
    callback_url = CONFIG.userbot_url if ctx.source == "userbot" else CONFIG.bot_url
    
    try:
        # Read file content (core has workspace access, bot/userbot don't need it)
        with open(path, 'rb') as f:
            file_content = f.read()
        
        filename = os.path.basename(path)
        
        async with aiohttp.ClientSession() as session:
            if ctx.source == "userbot":
                # Userbot expects JSON with base64
                import base64
                payload = {
                    "target": str(ctx.chat_id),
                    "file_data": base64.b64encode(file_content).decode('utf-8'),
                    "filename": filename,
                    "caption": caption or ""
                }
                async with session.post(
                    f"{callback_url}/send_file",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    data = await resp.json()
            else:
                # Bot expects multipart form
                form = aiohttp.FormData()
                form.add_field('chat_id', str(ctx.chat_id))
                form.add_field('caption', caption or "")
                form.add_field('file', file_content, filename=filename)
                
                async with session.post(
                    f"{callback_url}/send_file",
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    data = await resp.json()
            
            if data.get("success"):
                tool_logger.info(f"File sent: {filename}")
                return ToolResult(True, output=f"✅ File sent: {filename}")
            else:
                error = data.get("error") or data.get("message", "Failed to send")
                return ToolResult(False, error=error)
    except Exception as e:
        tool_logger.error(f"Send file error: {e}")
        return ToolResult(False, error=str(e))
