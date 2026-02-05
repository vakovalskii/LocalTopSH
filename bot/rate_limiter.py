"""Rate limiting for Telegram API"""

import asyncio
from config import CONFIG


class RateLimiter:
    def __init__(self):
        self.global_last_send = 0.0
        self.group_last_send: dict[int, float] = {}
        self.send_lock = asyncio.Lock()
        self.user_locks: dict[int, asyncio.Lock] = {}
        self.active_users: set[int] = set()
    
    async def safe_send(self, chat_id: int, coro):
        """Send with rate limiting"""
        async with self.send_lock:
            now = asyncio.get_event_loop().time()
            
            # Global rate limit
            global_wait = CONFIG.global_min_interval - (now - self.global_last_send)
            if global_wait > 0:
                await asyncio.sleep(global_wait)
            
            # Group rate limit
            if chat_id < 0:
                last_group = self.group_last_send.get(chat_id, 0)
                group_wait = CONFIG.group_min_interval - (now - last_group)
                if group_wait > 0:
                    await asyncio.sleep(group_wait)
                self.group_last_send[chat_id] = asyncio.get_event_loop().time()
            
            self.global_last_send = asyncio.get_event_loop().time()
            
            for attempt in range(CONFIG.max_retries):
                try:
                    return await coro
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "retry_after" in error_str.lower():
                        wait = 30 + 5  # default retry + buffer
                        print(f"[rate-limit] 429, waiting {wait}s ({attempt+1}/{CONFIG.max_retries})")
                        if attempt < CONFIG.max_retries - 1:
                            await asyncio.sleep(wait)
                    else:
                        print(f"[send] Error: {error_str[:100]}")
                        return None
            return None
    
    def get_user_lock(self, user_id: int) -> asyncio.Lock:
        if user_id not in self.user_locks:
            self.user_locks[user_id] = asyncio.Lock()
        return self.user_locks[user_id]
    
    def can_accept_user(self, user_id: int) -> bool:
        if user_id in self.active_users:
            return True
        return len(self.active_users) < CONFIG.max_concurrent
    
    def mark_active(self, user_id: int):
        self.active_users.add(user_id)
    
    def mark_inactive(self, user_id: int):
        self.active_users.discard(user_id)


# Singleton instance
rate_limiter = RateLimiter()
