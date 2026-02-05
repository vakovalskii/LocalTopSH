"""Web tools: search and fetch"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
from config import CONFIG
from logger import tool_logger
from models import ToolResult, ToolContext


async def tool_search_web(args: dict, ctx: ToolContext) -> ToolResult:
    """Search the web via proxy"""
    query = args.get("query", "")
    
    if not CONFIG.proxy_url:
        return ToolResult(False, error="No proxy configured")
    
    tool_logger.info(f"Web search: {query}")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{CONFIG.proxy_url}/zai/search?q={query}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    return ToolResult(False, error=f"Search failed: {resp.status}")
                data = await resp.json()
        
        results = data.get("search_result", [])
        if not results:
            return ToolResult(True, output="(no results)")
        
        output = []
        for i, r in enumerate(results[:10], 1):
            date = f" ({r.get('publish_date', '')})" if r.get('publish_date') else ""
            content = r.get("content", "")[:400]
            output.append(f"[{i}] {r.get('title', 'Untitled')}{date}\n{r.get('link', '')}\n{content}")
        
        tool_logger.info(f"Found {len(results)} results")
        return ToolResult(True, output="\n\n".join(output))
    except Exception as e:
        tool_logger.error(f"Web search error: {e}")
        return ToolResult(False, error=str(e))


async def tool_fetch_page(args: dict, ctx: ToolContext) -> ToolResult:
    """Fetch URL content"""
    url = args.get("url", "")
    
    # Block internal URLs
    blocked = ["169.254.169.254", "localhost", "127.", "10.", "192.168.", "172."]
    if any(b in url for b in blocked):
        return ToolResult(False, error="🚫 Internal URL blocked")
    
    tool_logger.info(f"Fetching: {url}")
    
    try:
        # Try Jina.ai reader
        jina_url = f"https://r.jina.ai/{url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(jina_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    tool_logger.info(f"Fetched via Jina: {len(content)} chars")
                    return ToolResult(True, output=content[:50000])
        
        # Fallback to direct fetch
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                content = await resp.text()
                tool_logger.info(f"Fetched directly: {len(content)} chars")
                return ToolResult(True, output=content[:50000])
    except Exception as e:
        tool_logger.error(f"Fetch error: {e}")
        return ToolResult(False, error=str(e))
