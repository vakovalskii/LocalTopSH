#!/usr/bin/env python3
"""
LocalTopSH Telegram Bot (Python/aiogram)
Entry point - orchestrates all modules
"""

import asyncio
from aiogram import types
from aiohttp import web

from config import TELEGRAM_TOKEN, CORE_URL, BOT_PORT, CONFIG
import state
from state import bot, dp
from server import create_http_app
from thoughts import start_thoughts_task

# Import handlers to register them with dispatcher
import handlers  # noqa: F401


async def main():
    if not TELEGRAM_TOKEN:
        print("Missing TELEGRAM_TOKEN")
        return
    
    # Get bot info
    me = await bot.get_me()
    state.bot_username = me.username or ""
    state.bot_id = me.id
    
    print("")
    print("=" * 50)
    print("LocalTopSH Bot (Python)")
    print("=" * 50)
    print(f"Bot: @{state.bot_username} ({state.bot_id})")
    print(f"Core: {CORE_URL}")
    print(f"HTTP: http://0.0.0.0:{BOT_PORT}")
    print(f"Max concurrent: {CONFIG.max_concurrent}")
    print("=" * 50)
    print("")
    
    # Set commands
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Start / Help"),
        types.BotCommand(command="clear", description="Clear session"),
        types.BotCommand(command="status", description="Show status"),
    ])
    
    # Start HTTP server
    http_app = create_http_app()
    runner = web.AppRunner(http_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", BOT_PORT)
    await site.start()
    print(f"[bot] HTTP server on http://0.0.0.0:{BOT_PORT}")
    
    # Start autonomous thoughts
    thoughts_task = start_thoughts_task()
    print(f"[bot] Thoughts task started")
    
    # Start polling
    print(f"[bot] Started, connecting to core at {CORE_URL}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
