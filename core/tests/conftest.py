"""Test configuration"""

import sys
import os

# Add core root to path so tests can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set environment for tests
os.environ.setdefault("WORKSPACE", "/tmp/test_workspace")
os.environ.setdefault("PROXY_URL", "http://proxy:3200")
os.environ.setdefault("BOT_URL", "http://bot:4001")
os.environ.setdefault("USERBOT_URL", "http://userbot:8080")
os.environ.setdefault("WORKSPACE_HOST_PATH", "/home/ubuntu/LocalTopSH/workspace")
