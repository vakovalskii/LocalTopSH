"""
Tools API - Single source of truth for agent tools

Provides:
- Built-in tool definitions
- MCP server management
- Skills system (Anthropic-style)
- Dynamic tool loading
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.mcp import mcp_cache
from src.skills import skills_manager
from src.routes import tools_router, mcp_router, skills_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("[tools-api] Starting up...")
    mcp_cache.load_cache()
    skills_manager.load_cache()
    skills_manager.scan_all()
    print(f"[tools-api] Loaded {len(mcp_cache.tools)} MCP tools, {len(skills_manager.skills)} skills")
    
    yield
    
    # Shutdown
    print("[tools-api] Shutting down...")


app = FastAPI(
    title="Tools API",
    version="3.0",
    description="Single source of truth for agent tools, MCP servers, and skills",
    lifespan=lifespan
)


# Health check
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "3.0",
        "mcp_enabled": True,
        "skills_enabled": True
    }


# Include routers
app.include_router(tools_router)
app.include_router(mcp_router)
app.include_router(skills_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
