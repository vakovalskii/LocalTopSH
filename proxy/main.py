"""
API Proxy - isolates secrets from agent container
Reads secrets from /run/secrets/ (Docker Secrets)
Agent sees only http://proxy:3200, no API keys
"""

import os
import asyncio
import aiohttp
from aiohttp import web
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[proxy] %(message)s'
)
log = logging.getLogger(__name__)

PORT = int(os.getenv("PROXY_PORT", "3200"))


def read_secret(name: str) -> str | None:
    """Read secret from file (Docker Secrets mount at /run/secrets/)"""
    paths = [
        f"/run/secrets/{name}",
        f"/run/secrets/{name}.txt",
        f"./secrets/{name}.txt",
        f"/app/secrets/{name}.txt",
    ]
    
    for path in paths:
        try:
            with open(path, 'r') as f:
                value = f.read().strip()
                if value:
                    log.info(f"Secret '{name}' loaded from {path}")
                    return value
        except (FileNotFoundError, PermissionError):
            continue
    
    # Fallback to env (insecure)
    env_name = name.upper()
    if os.getenv(env_name):
        log.warning(f"Secret '{name}' loaded from env (INSECURE)")
        return os.getenv(env_name)
    
    log.warning(f"WARNING: Secret '{name}' not found!")
    return None


# Load secrets at startup
LLM_BASE_URL = read_secret("base_url")
LLM_API_KEY = read_secret("api_key")
ZAI_API_KEY = read_secret("zai_api_key")


async def health(request: web.Request) -> web.Response:
    """Health check endpoint"""
    return web.json_response({
        "status": "ok",
        "llm": bool(LLM_BASE_URL),
        "zai": bool(ZAI_API_KEY)
    })


import json

LOG_RAW = os.getenv("LOG_RAW", "false").lower() == "true"

async def proxy_llm(request: web.Request) -> web.StreamResponse:
    """Proxy /v1/* requests to LLM API with auth"""
    if not LLM_BASE_URL:
        return web.json_response({"error": "LLM not configured"}, status=500)
    
    # Build target URL
    path = request.match_info.get("path", "")
    target_url = LLM_BASE_URL.rstrip("/v1").rstrip("/") + "/v1/" + path
    if request.query_string:
        target_url += "?" + request.query_string
    
    log.info(f"LLM: {request.method} /v1/{path}")
    
    # Forward headers (except host and connection)
    headers = dict(request.headers)
    headers.pop("Host", None)
    headers.pop("Connection", None)
    headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Read request body
            body = await request.read()
            
            # Log raw request if enabled
            if LOG_RAW and body:
                try:
                    data = json.loads(body)
                    log.info("=" * 80)
                    log.info("RAW LLM REQUEST:")
                    log.info(f"  model: {data.get('model', '?')}")
                    
                    messages = data.get("messages", [])
                    log.info(f"  messages: {len(messages)}")
                    for i, msg in enumerate(messages):
                        role = msg.get("role", "?")
                        content = msg.get("content", "")
                        tool_calls = msg.get("tool_calls", [])
                        tool_call_id = msg.get("tool_call_id", "")
                        
                        if role == "system":
                            log.info(f"    [{i}] SYSTEM ({len(content)} chars):")
                            # Print first 500 and last 200 chars
                            if len(content) > 800:
                                log.info(f"      {content[:500]}")
                                log.info(f"      ... [{len(content)-700} chars] ...")
                                log.info(f"      {content[-200:]}")
                            else:
                                for line in content.split('\n')[:30]:
                                    log.info(f"      {line}")
                        elif role == "user":
                            log.info(f"    [{i}] USER:")
                            for line in content.split('\n'):
                                log.info(f"      {line}")
                        elif role == "assistant":
                            if tool_calls:
                                log.info(f"    [{i}] ASSISTANT (tool_calls):")
                                for tc in tool_calls:
                                    fn = tc.get("function", {})
                                    log.info(f"      → {fn.get('name')}({fn.get('arguments', '')})")
                            elif content:
                                log.info(f"    [{i}] ASSISTANT:")
                                for line in content.split('\n'):
                                    log.info(f"      {line}")
                            else:
                                log.info(f"    [{i}] ASSISTANT: (empty)")
                        elif role == "tool":
                            log.info(f"    [{i}] TOOL [{tool_call_id[:12]}]:")
                            # Truncate long tool output
                            if len(content) > 500:
                                log.info(f"      {content[:400]}")
                                log.info(f"      ... [{len(content)-400} chars more] ...")
                            else:
                                for line in content.split('\n')[:20]:
                                    log.info(f"      {line}")
                    
                    tools = data.get("tools", [])
                    log.info(f"  tools: {len(tools)} definitions")
                    for t in tools:
                        fn = t.get("function", {})
                        log.info(f"    - {fn.get('name')}")
                    
                    log.info("=" * 80)
                except Exception as e:
                    log.warning(f"Failed to parse request body: {e}")
            
            # Collect response for logging
            response_chunks = []
            
            async with session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=body,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                # Stream response
                response = web.StreamResponse(
                    status=resp.status,
                    headers={k: v for k, v in resp.headers.items() 
                            if k.lower() not in ('transfer-encoding', 'content-encoding')}
                )
                await response.prepare(request)
                
                async for chunk in resp.content.iter_any():
                    if LOG_RAW:
                        response_chunks.append(chunk)
                    await response.write(chunk)
                
                await response.write_eof()
                
                # Log raw response
                if LOG_RAW and response_chunks:
                    try:
                        full_response = b''.join(response_chunks)
                        data = json.loads(full_response)
                        log.info("=" * 80)
                        log.info("RAW LLM RESPONSE:")
                        log.info(f"  id: {data.get('id', '?')}")
                        log.info(f"  model: {data.get('model', '?')}")
                        
                        for i, choice in enumerate(data.get("choices", [])):
                            msg = choice.get("message", {})
                            finish = choice.get("finish_reason", "?")
                            content = msg.get("content", "")
                            tool_calls = msg.get("tool_calls", [])
                            
                            log.info(f"  choice[{i}] finish_reason: {finish}")
                            
                            if tool_calls:
                                log.info(f"  choice[{i}] tool_calls:")
                                for tc in tool_calls:
                                    fn = tc.get("function", {})
                                    log.info(f"    → {fn.get('name')}({fn.get('arguments', '')})")
                            
                            if content:
                                log.info(f"  choice[{i}] content:")
                                for line in content.split('\n'):
                                    log.info(f"    {line}")
                        
                        usage = data.get("usage", {})
                        log.info(f"  usage: prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}, total={usage.get('total_tokens')}")
                        log.info("=" * 80)
                    except Exception as e:
                        log.warning(f"Failed to parse response: {e}")
                
                return response
                
    except asyncio.TimeoutError:
        return web.json_response({"error": "LLM request timeout"}, status=504)
    except Exception as e:
        log.error(f"LLM proxy error: {e}")
        return web.json_response({"error": "Proxy error", "message": str(e)}, status=502)


async def zai_request(endpoint: str, body: dict) -> tuple[int, dict]:
    """Make request to Z.AI API"""
    url = f"https://api.z.ai/api/paas/v4/{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ZAI_API_KEY}"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                try:
                    data = await resp.json()
                except:
                    data = {"raw": await resp.text()}
                return resp.status, data
    except Exception as e:
        raise Exception(f"ZAI request failed: {e}")


async def zai_search(request: web.Request) -> web.Response:
    """Z.AI Web Search: /zai/search?q=..."""
    if not ZAI_API_KEY:
        return web.json_response({"error": "ZAI not configured"}, status=500)
    
    query = request.query.get("q", "")
    log.info(f'ZAI search: "{query[:50]}..."')
    
    try:
        status, data = await zai_request("web_search", {
            "search_engine": "search-prime",
            "search_query": query,
            "count": 10
        })
        return web.json_response(data, status=status)
    except Exception as e:
        log.error(f"ZAI error: {e}")
        return web.json_response({"error": "ZAI request failed", "message": str(e)}, status=502)


async def zai_read(request: web.Request) -> web.Response:
    """Z.AI Web Reader: /zai/read?url=..."""
    if not ZAI_API_KEY:
        return web.json_response({"error": "ZAI not configured"}, status=500)
    
    page_url = request.query.get("url", "")
    log.info(f'ZAI read: "{page_url[:50]}..."')
    
    try:
        status, data = await zai_request("reader", {
            "url": page_url,
            "return_format": "markdown",
            "retain_images": False,
            "timeout": 30
        })
        return web.json_response(data, status=status)
    except Exception as e:
        log.error(f"ZAI error: {e}")
        return web.json_response({"error": "ZAI request failed", "message": str(e)}, status=502)


async def not_found(request: web.Request) -> web.Response:
    """Handle unknown routes"""
    return web.json_response({
        "error": "Not found",
        "routes": ["/v1/*", "/zai/search?q=...", "/zai/read?url=...", "/health"]
    }, status=404)


def create_app() -> web.Application:
    """Create aiohttp application"""
    app = web.Application()
    
    # Routes
    app.router.add_get("/health", health)
    app.router.add_route("*", "/v1/{path:.*}", proxy_llm)
    app.router.add_get("/zai/search", zai_search)
    app.router.add_get("/zai/read", zai_read)
    
    # Catch-all for 404
    app.router.add_route("*", "/{path:.*}", not_found)
    
    return app


def main():
    log.info("Starting API proxy...")
    log.info(f"LLM endpoint: {'✓ configured' if LLM_BASE_URL else '✗ NOT SET'}")
    log.info(f"ZAI API: {'✓ configured' if ZAI_API_KEY else '✗ NOT SET'}")
    
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=PORT, print=lambda x: log.info(x))


if __name__ == "__main__":
    main()
