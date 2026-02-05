"""Task manager (TODO list)"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import tool_logger
from models import ToolResult, ToolContext


# Per-session task storage
session_tasks: dict[str, list[dict]] = {}


async def tool_manage_tasks(args: dict, ctx: ToolContext) -> ToolResult:
    """Manage todo tasks"""
    action = args.get("action", "list")
    session_id = ctx.session_id or "default"
    
    if session_id not in session_tasks:
        session_tasks[session_id] = []
    
    tasks = session_tasks[session_id]
    
    if action == "add":
        content = args.get("content", "")
        if not content:
            return ToolResult(False, error="Content required")
        
        task_id = f"t{len(tasks) + 1}"
        tasks.append({"id": task_id, "content": content, "status": "pending"})
        tool_logger.info(f"Added task {task_id}: {content[:50]}...")
        return ToolResult(True, output=f"Added task {task_id}: {content}")
    
    elif action == "update":
        task_id = args.get("id")
        status = args.get("status")
        if not task_id:
            return ToolResult(False, error="Task ID required")
        
        for t in tasks:
            if t["id"] == task_id:
                if status:
                    t["status"] = status
                tool_logger.info(f"Updated task {task_id}: {status}")
                return ToolResult(True, output=f"Updated {task_id}")
        return ToolResult(False, error="Task not found")
    
    elif action == "list":
        if not tasks:
            return ToolResult(True, output="No tasks")
        lines = [f"[{t['status']}] {t['id']}: {t['content']}" for t in tasks]
        return ToolResult(True, output="\n".join(lines))
    
    elif action == "clear":
        session_tasks[session_id] = []
        tool_logger.info(f"Tasks cleared for {session_id}")
        return ToolResult(True, output="Tasks cleared")
    
    return ToolResult(False, error=f"Unknown action: {action}")
