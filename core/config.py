"""Core configuration"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Central configuration"""
    # API
    api_port: int = 4000
    proxy_url: str = ""
    model: str = "openai/gpt-oss-120b"
    
    # Agent
    max_iterations: int = 30
    max_history: int = 10
    max_tool_output: int = 8000
    max_context_messages: int = 40
    max_blocked_commands: int = 3
    
    # Timeouts (seconds)
    tool_timeout: int = 120
    command_timeout: int = 60
    web_timeout: int = 30
    
    # Storage
    max_memory_chars: int = 4000
    max_chat_history_chars: int = 15000
    max_chat_messages: int = 200
    
    # Paths
    workspace: str = "/workspace"
    shared_dir: str = "/workspace/_shared"
    
    # Callbacks
    bot_url: str = "http://bot:4001"
    userbot_url: str = "http://userbot:8080"


CONFIG = Config(
    api_port=int(os.getenv("API_PORT", "4000")),
    proxy_url=os.getenv("PROXY_URL", ""),
    model=os.getenv("MODEL_NAME", "openai/gpt-oss-120b"),
    workspace=os.getenv("WORKSPACE", "/workspace"),
    bot_url=os.getenv("BOT_URL", "http://bot:4001"),
    userbot_url=os.getenv("USERBOT_URL", "http://userbot:8080"),
)
