"""Core Agent Entry Point"""

import asyncio
import uvicorn
from config import CONFIG
from logger import core_logger


async def init_sandbox():
    """Initialize Docker sandbox manager"""
    try:
        from tools.sandbox import start_sandbox_manager
        from tools.bash import set_sandbox_enabled
        
        sandbox_ready = await start_sandbox_manager()
        set_sandbox_enabled(sandbox_ready)
        return sandbox_ready
    except Exception as e:
        core_logger.warning(f"Sandbox init failed: {e}")
        return False


def main():
    core_logger.info("=" * 60)
    core_logger.info("LocalTopSH Core Agent")
    core_logger.info("=" * 60)
    core_logger.info(f"Port: {CONFIG.api_port}")
    core_logger.info(f"Model: {CONFIG.model}")
    core_logger.info(f"Proxy: {CONFIG.proxy_url}")
    core_logger.info(f"Workspace: {CONFIG.workspace}")
    
    # Initialize sandbox
    sandbox_ok = asyncio.run(init_sandbox())
    core_logger.info(f"Sandbox: {'ENABLED' if sandbox_ok else 'DISABLED (fallback to local)'}")
    core_logger.info("=" * 60)
    
    # Import api to register routes
    from api import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=CONFIG.api_port,
        log_level="warning"
    )


if __name__ == "__main__":
    main()
