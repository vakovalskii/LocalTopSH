"""Tool registry and common types"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from typing import Callable, Any
from logger import log_tool_call, log_tool_result
from config import CONFIG
from models import ToolResult, ToolContext


# Tool definitions for OpenAI
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command. Use for: git, npm, pip, python, system ops.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents. Always read before editing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"},
                    "offset": {"type": "integer", "description": "Starting line (1-based)"},
                    "limit": {"type": "integer", "description": "Number of lines"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to file. Creates if doesn't exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit file by replacing text. old_text must match exactly.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"},
                    "old_text": {"type": "string", "description": "Text to find"},
                    "new_text": {"type": "string", "description": "Replacement text"}
                },
                "required": ["path", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file within workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files by glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern (e.g. **/*.py)"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_text",
            "description": "Search text in files using grep.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Text/regex to search"},
                    "path": {"type": "string", "description": "Directory to search"},
                    "ignore_case": {"type": "boolean", "description": "Case insensitive"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List directory contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the internet for current info, news, docs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_page",
            "description": "Fetch and parse URL content as markdown.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "memory",
            "description": "Long-term memory. Save/read important info across sessions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["read", "append", "clear"]},
                    "content": {"type": "string", "description": "Text to save (for append)"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_task",
            "description": "Schedule reminders or recurring tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["add", "list", "cancel"]},
                    "type": {"type": "string", "enum": ["message", "command", "agent"]},
                    "content": {"type": "string", "description": "Task content"},
                    "delay_minutes": {"type": "integer", "description": "Delay before execution"},
                    "recurring": {"type": "boolean", "description": "Repeat task"},
                    "interval_minutes": {"type": "integer", "description": "Repeat interval"},
                    "task_id": {"type": "string", "description": "Task ID for cancel"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_tasks",
            "description": "Todo list for planning complex tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["add", "update", "list", "clear"]},
                    "id": {"type": "string", "description": "Task ID"},
                    "content": {"type": "string", "description": "Task description"},
                    "status": {"type": "string", "enum": ["pending", "done", "cancelled"]}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_file",
            "description": "Send a file from workspace to the chat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file in workspace"},
                    "caption": {"type": "string", "description": "Optional caption"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_dm",
            "description": "Send a private message to current user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "integer", "description": "User ID (usually current user)"},
                    "text": {"type": "string", "description": "Message text"}
                },
                "required": ["user_id", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "manage_message",
            "description": "Edit or delete bot messages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["edit", "delete"]},
                    "message_id": {"type": "integer", "description": "Message ID to edit/delete"},
                    "text": {"type": "string", "description": "New text (for edit)"}
                },
                "required": ["action", "message_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": "Ask user a question and wait for their answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Question to ask"},
                    "timeout": {"type": "integer", "description": "Seconds to wait (default 60)"}
                },
                "required": ["question"]
            }
        }
    }
]


# Import tool executors (done after class definitions to avoid circular imports)
from tools.bash import tool_run_command
from tools.files import tool_read_file, tool_write_file, tool_edit_file, tool_delete_file, tool_search_files, tool_search_text, tool_list_directory
from tools.web import tool_search_web, tool_fetch_page
from tools.memory import tool_memory
from tools.scheduler import tool_schedule_task
from tools.tasks import tool_manage_tasks
from tools.send_file import tool_send_file
from tools.send_dm import tool_send_dm
from tools.message import tool_manage_message
from tools.ask_user import tool_ask_user


# Tool registry
TOOL_EXECUTORS = {
    "run_command": tool_run_command,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "edit_file": tool_edit_file,
    "delete_file": tool_delete_file,
    "search_files": tool_search_files,
    "search_text": tool_search_text,
    "list_directory": tool_list_directory,
    "search_web": tool_search_web,
    "fetch_page": tool_fetch_page,
    "memory": tool_memory,
    "schedule_task": tool_schedule_task,
    "manage_tasks": tool_manage_tasks,
    "send_file": tool_send_file,
    "send_dm": tool_send_dm,
    "manage_message": tool_manage_message,
    "ask_user": tool_ask_user,
}


async def execute_tool(name: str, args: dict, ctx: ToolContext) -> ToolResult:
    """Execute a tool by name"""
    executor = TOOL_EXECUTORS.get(name)
    if not executor:
        return ToolResult(False, error=f"Unknown tool: {name}")
    
    log_tool_call(name, args)
    
    try:
        result = await asyncio.wait_for(
            executor(args, ctx),
            timeout=CONFIG.tool_timeout
        )
        
        log_tool_result(result.success, result.output, result.error)
        return result
        
    except asyncio.TimeoutError:
        return ToolResult(False, error=f"Tool {name} timed out")
    except Exception as e:
        return ToolResult(False, error=str(e))
