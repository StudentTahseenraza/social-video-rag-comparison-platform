from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
import uuid
from app.utils.helpers import setup_logging

logger = setup_logging()

class TaskQueue:
    """Simple in-memory task queue for demo (replace with Celery for production)"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.background_tasks: set = set()
    
    def create_task(self, task_type: str, data: Dict[str, Any]) -> str:
        """Create a new task and return task ID"""
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = {
            'id': task_id,
            'type': task_type,
            'data': data,
            'status': 'pending',
            'created_at': datetime.now(),
            'result': None,
            'error': None
        }
        return task_id
    
    async def run_background(self, coroutine, task_id: str):
        """Run a coroutine in background"""
        task = asyncio.create_task(self._execute_task(coroutine, task_id))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
    
    async def _execute_task(self, coroutine, task_id: str):
        """Execute task and update status"""
        try:
            self.tasks[task_id]['status'] = 'running'
            result = await coroutine
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['result'] = result
        except Exception as e:
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            logger.error(f"Task {task_id} failed: {str(e)}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        return self.tasks.get(task_id)

# Global task queue instance
task_queue = TaskQueue()