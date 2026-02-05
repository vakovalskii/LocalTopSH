"""Memory tool for persistent storage"""

import sys
import os as os_module
sys.path.insert(0, os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__))))

import os
from datetime import datetime
from logger import tool_logger
from models import ToolResult, ToolContext


async def tool_memory(args: dict, ctx: ToolContext) -> ToolResult:
    """Long-term memory"""
    action = args.get("action", "read")
    content = args.get("content", "")
    memory_path = os.path.join(ctx.cwd, "MEMORY.md")
    
    tool_logger.info(f"Memory action: {action}")
    
    try:
        if action == "read":
            if not os.path.exists(memory_path):
                return ToolResult(True, output="(memory is empty)")
            with open(memory_path, "r") as f:
                return ToolResult(True, output=f.read() or "(memory is empty)")
        
        elif action == "append":
            if not content:
                return ToolResult(False, error="Content required")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            entry = f"\n## {timestamp}\n{content}\n"
            
            existing = ""
            if os.path.exists(memory_path):
                with open(memory_path, "r") as f:
                    existing = f.read()
            else:
                existing = "# Agent Memory\n\nNotes from previous sessions.\n"
            
            with open(memory_path, "w") as f:
                f.write(existing + entry)
            
            tool_logger.info(f"Added {len(content)} chars to memory")
            return ToolResult(True, output=f"Added to memory ({len(content)} chars)")
        
        elif action == "clear":
            header = "# Agent Memory\n\nNotes from previous sessions.\n"
            with open(memory_path, "w") as f:
                f.write(header)
            tool_logger.info("Memory cleared")
            return ToolResult(True, output="Memory cleared")
        
        return ToolResult(False, error=f"Unknown action: {action}")
    except Exception as e:
        return ToolResult(False, error=str(e))
