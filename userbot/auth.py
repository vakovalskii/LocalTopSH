"""
First-time authorization script
Run this LOCALLY (not in Docker) to create session file
Then the session can be used in Docker without interactive login
"""

import os
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession

# Read from secrets or ask
def get_secret(name, prompt):
    path = f'../secrets/{name}.txt'
    if os.path.exists(path):
        with open(path) as f:
            value = f.read().strip()
            if value:
                return value
    return input(f"{prompt}: ")

print("=" * 50)
print("Telegram Userbot Authorization")
print("=" * 50)
print()

api_id = get_secret('telegram_api_id', 'API ID')
api_hash = get_secret('telegram_api_hash', 'API Hash')
phone = get_secret('telegram_phone', 'Phone (with country code, e.g. +79001234567)')

print()
print(f"API ID: {api_id}")
print(f"Phone: {phone}")
print()

# Create session directory
os.makedirs('session', exist_ok=True)

# Create client and authorize
client = TelegramClient('session/userbot', int(api_id), api_hash)

async def main():
    from telethon.errors import FloodWaitError
    
    try:
        await client.start(phone=phone)
    except FloodWaitError as e:
        print(f"\n⚠️ FloodWait: Need to wait {e.seconds} seconds")
        print(f"   Telegram blocked requests due to too many attempts")
        print(f"\n   Please wait and try again in {e.seconds // 60} min {e.seconds % 60} sec")
        return
    
    me = await client.get_me()
    print()
    print("=" * 50)
    print(f"✅ Authorized as @{me.username} ({me.id})")
    print("=" * 50)
    print()
    print("Session saved to: session/userbot.session")
    print()
    print("Now you can run userbot in Docker:")
    print("  docker compose --profile userbot up -d")
    print()
    
    await client.disconnect()

import asyncio
asyncio.run(main())
