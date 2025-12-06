import uuid
import time
import asyncio
from typing import Dict, Optional, List
from core.a2a import Task, TaskState, TaskStatus, Message, Role, Part

class TaskManager:
    def __init__(self):
        # In-memory storage for now. In production, this should be a persistent DB.
        self._tasks: Dict[str, Task] = {}

    def create_task(self, context_id: Optional[str] = None) -> Task:
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(
                state=TaskState.SUBMITTED,
                timestamp=time.time()
            )
        )
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def update_task_status(self, task_id: str, state: str, message: Optional[Message] = None):
        task = self._tasks.get(task_id)
        if task:
            task.status.state = state
            task.status.timestamp = time.time()
            if message:
                task.status.message = message
                # Append to history as well? standard says status.message is implicit "newest"
                # But let's keep history simple for now.
                task.history.append(message)
    
    def add_message_to_task(self, task_id: str, message: Message):
        task = self._tasks.get(task_id)
        if task:
            task.history.append(message)

    def list_tasks(self, limit: int = 10) -> List[Task]:
        # Simple list implementation
        return list(self._tasks.values())[:limit]

# Global instance
task_manager = TaskManager()
