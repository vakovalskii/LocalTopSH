"""Task scheduler"""

import sys
import os as os_module
sys.path.insert(0, os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__))))

import os
import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable
from logger import scheduler_logger
from models import ToolResult, ToolContext


@dataclass
class ScheduledTask:
    id: str
    user_id: int
    chat_id: int
    task_type: str  # 'message', 'command', 'agent'
    content: str
    execute_at: float
    created_at: float
    recurring: bool = False
    interval_minutes: int = 0
    source: str = "bot"


class Scheduler:
    def __init__(self):
        self.tasks: dict[str, ScheduledTask] = {}
        self.user_tasks: dict[int, set[str]] = {}
        self.send_message_callback: Optional[Callable] = None
        self.send_userbot_callback: Optional[Callable] = None
        self.run_agent_callback: Optional[Callable] = None
        self.running = False
    
    def set_callbacks(
        self,
        send_message: Optional[Callable] = None,
        send_userbot: Optional[Callable] = None,
        run_agent: Optional[Callable] = None
    ):
        if send_message:
            self.send_message_callback = send_message
        if send_userbot:
            self.send_userbot_callback = send_userbot
        if run_agent:
            self.run_agent_callback = run_agent
        scheduler_logger.info("Callbacks configured")
    
    async def start(self):
        if self.running:
            return
        self.running = True
        scheduler_logger.info("Scheduler started")
        
        while self.running:
            await asyncio.sleep(5)
            now = datetime.now().timestamp()
            
            for task_id, task in list(self.tasks.items()):
                if task.execute_at <= now:
                    scheduler_logger.info(f"Executing task: {task_id}")
                    await self._execute_task(task)
                    
                    if task.recurring and task.interval_minutes:
                        task.execute_at = now + task.interval_minutes * 60
                        scheduler_logger.info(f"Task {task_id} rescheduled")
                    else:
                        self.tasks.pop(task_id, None)
                        if task.user_id in self.user_tasks:
                            self.user_tasks[task.user_id].discard(task_id)
    
    async def _execute_task(self, task: ScheduledTask):
        try:
            is_userbot = task.source == "userbot"
            
            if task.task_type == "message":
                text = f"⏰ Напоминание: {task.content}"
                if is_userbot and self.send_userbot_callback:
                    await self.send_userbot_callback(task.chat_id, text)
                    scheduler_logger.info(f"Sent reminder via userbot to {task.chat_id}")
                elif self.send_message_callback:
                    await self.send_message_callback(task.chat_id, text)
                    scheduler_logger.info(f"Sent reminder via bot to {task.chat_id}")
            
            elif task.task_type == "agent" and self.run_agent_callback:
                prompt = f"⏰ Scheduled task: {task.content}"
                await self.run_agent_callback(task.user_id, task.chat_id, prompt, task.source)
                scheduler_logger.info(f"Ran agent task for {task.user_id}")
        
        except Exception as e:
            scheduler_logger.error(f"Task {task.id} failed: {e}")
    
    def add_task(
        self,
        user_id: int,
        chat_id: int,
        task_type: str,
        content: str,
        delay_minutes: int,
        recurring: bool = False,
        interval_minutes: int = 0,
        source: str = "bot"
    ) -> tuple[bool, str]:
        # Check limit
        user_task_set = self.user_tasks.get(user_id, set())
        if len(user_task_set) >= 10:
            return False, "Max 10 tasks per user"
        
        task_id = f"task_{int(datetime.now().timestamp())}_{os.urandom(3).hex()}"
        now = datetime.now().timestamp()
        
        task = ScheduledTask(
            id=task_id,
            user_id=user_id,
            chat_id=chat_id,
            task_type=task_type,
            content=content,
            execute_at=now + delay_minutes * 60,
            created_at=now,
            recurring=recurring,
            interval_minutes=max(interval_minutes, 30) if recurring else 0,
            source=source
        )
        
        self.tasks[task_id] = task
        if user_id not in self.user_tasks:
            self.user_tasks[user_id] = set()
        self.user_tasks[user_id].add(task_id)
        
        execute_time = datetime.fromtimestamp(task.execute_at).strftime("%H:%M")
        recur_info = f" (repeat every {interval_minutes}min)" if recurring else " (once)"
        
        scheduler_logger.info(f"Added task {task_id} for user {user_id}: {content[:50]}...")
        return True, f"✅ Scheduled at {execute_time}{recur_info}\nID: {task_id}"
    
    def list_tasks(self, user_id: int) -> str:
        user_task_ids = self.user_tasks.get(user_id, set())
        if not user_task_ids:
            return "No scheduled tasks"
        
        lines = []
        now = datetime.now().timestamp()
        for tid in user_task_ids:
            task = self.tasks.get(tid)
            if task:
                time_left = int((task.execute_at - now) / 60)
                recur = f" 🔄 every {task.interval_minutes}min" if task.recurring else ""
                icon = "👤" if task.source == "userbot" else "🤖"
                lines.append(f"• {tid}: {icon} [{task.task_type}] in {time_left}min{recur}\n  \"{task.content[:50]}\"")
        
        return f"Scheduled tasks ({len(lines)}):\n" + "\n".join(lines)
    
    def cancel_task(self, user_id: int, task_id: str) -> tuple[bool, str]:
        task = self.tasks.get(task_id)
        if not task:
            return False, "Task not found"
        if task.user_id != user_id:
            return False, "Cannot cancel other user's task"
        
        self.tasks.pop(task_id)
        if user_id in self.user_tasks:
            self.user_tasks[user_id].discard(task_id)
        
        scheduler_logger.info(f"Task {task_id} cancelled")
        return True, f"Task {task_id} cancelled"


# Global scheduler instance
scheduler = Scheduler()


async def tool_schedule_task(args: dict, ctx: ToolContext) -> ToolResult:
    """Schedule tasks"""
    action = args.get("action", "list")
    
    if action == "add":
        task_type = args.get("type")
        content = args.get("content")
        if not task_type or not content:
            return ToolResult(False, error="Need type and content")
        
        delay = args.get("delay_minutes", 1)
        recurring = args.get("recurring", False)
        interval = args.get("interval_minutes", 60)
        
        ok, msg = scheduler.add_task(
            ctx.user_id, ctx.chat_id, task_type, content,
            delay, recurring, interval, ctx.source
        )
        return ToolResult(ok, output=msg if ok else "", error="" if ok else msg)
    
    elif action == "list":
        return ToolResult(True, output=scheduler.list_tasks(ctx.user_id))
    
    elif action == "cancel":
        task_id = args.get("task_id")
        if not task_id:
            return ToolResult(False, error="Need task_id")
        ok, msg = scheduler.cancel_task(ctx.user_id, task_id)
        return ToolResult(ok, output=msg if ok else "", error="" if ok else msg)
    
    return ToolResult(False, error=f"Unknown action: {action}")
