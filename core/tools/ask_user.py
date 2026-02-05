"""Ask user for input interactively"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import aiohttp
from datetime import datetime
from config import CONFIG
from logger import tool_logger
from models import ToolResult, ToolContext


async def tool_ask_user(args: dict, ctx: ToolContext) -> ToolResult:
    """Ask user a question and wait for answer"""
    question = args.get("question", "")
    timeout_seconds = args.get("timeout", 60)
    
    if not question:
        return ToolResult(False, error="question required")
    
    # Limit timeout
    timeout_seconds = min(max(timeout_seconds, 10), 120)
    
    callback_url = CONFIG.userbot_url if ctx.source == "userbot" else CONFIG.bot_url
    question_id = f"q_{ctx.user_id}_{int(datetime.now().timestamp())}"
    
    tool_logger.info(f"Asking user {ctx.user_id}: {question[:50]}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Register question
            async with session.post(
                f"{callback_url}/ask",
                json={
                    "question_id": question_id,
                    "chat_id": ctx.chat_id,
                    "user_id": ctx.user_id,
                    "question": question
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()
                if not data.get("success"):
                    return ToolResult(False, error=data.get("error", "Failed to ask"))
            
            # Poll for answer
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout_seconds:
                await asyncio.sleep(2)  # Check every 2 seconds
                
                async with session.get(
                    f"{callback_url}/answer/{question_id}",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    data = await resp.json()
                    if data.get("answered"):
                        answer = data.get("answer", "")
                        tool_logger.info(f"Got answer: {answer[:50]}...")
                        return ToolResult(True, output=f"User answered: {answer}")
            
            # Timeout
            tool_logger.info(f"Question {question_id} timed out")
            return ToolResult(True, output="(no answer - user didn't respond in time)")
    
    except Exception as e:
        tool_logger.error(f"Ask user error: {e}")
        return ToolResult(False, error=str(e))
