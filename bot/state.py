"""Global bot state"""

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import TELEGRAM_TOKEN


# Bot instance
bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Dispatcher
dp = Dispatcher()

# Bot info (set on startup)
bot_username = ""
bot_id = 0

# AFK state
afk_until = 0.0
afk_reason = ""

# Anti-loop tracking
bot_conversation_count: dict[tuple[int, int], int] = {}
bot_conversation_reset: dict[tuple[int, int], float] = {}


def is_afk() -> bool:
    """Check if bot is in AFK mode"""
    return afk_until > 0 and asyncio.get_event_loop().time() < afk_until


def set_afk(minutes: int, reason: str):
    """Set AFK mode"""
    global afk_until, afk_reason
    if minutes <= 0:
        afk_until = 0
        afk_reason = ""
    else:
        afk_until = asyncio.get_event_loop().time() + minutes * 60
        afk_reason = reason


def clear_afk():
    """Clear AFK mode"""
    global afk_until, afk_reason
    afk_until = 0
    afk_reason = ""
