import httpx
import asyncio
import uuid
import logging
from typing import Dict, Any, Optional
from core.a2a import JsonRpcRequest, JsonRpcResponse, Message, Task, TaskState

logger = logging.getLogger(__name__)

class A2AClient:
    """
    Client for interacting with other A2A-compliant agents.
    Implements JSON-RPC 2.0 over HTTP.
    """
    def __init__(self, agent_url: str, timeout: int = 30):
        self.agent_url = agent_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "DKMES-A2A-Client/1.0"
        }

    async def get_agent_card(self) -> Dict[str, Any]:
        """Fetch the agent's capabilities card."""
        try:
            url = f"{self.agent_url}/.well-known/agent.json"
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch Agent Card from {self.agent_url}: {e}")
            raise

    async def send_message(self, message: Dict[str, Any], context_id: Optional[str] = None) -> Task:
        """
        Send a message to the agent to start a task.
        Method: message/send
        """
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "method": "message/send",
            "params": {
                "message": message,
                "contextId": context_id
            },
            "id": request_id
        }
        
        rpc_resp = await self._post_rpc(payload)
        task_data = rpc_resp.result
        return Task(**task_data)

    async def get_task(self, task_id: str) -> Task:
        """
        Get the current status of a task.
        Method: tasks/get
        """
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/get",
            "params": {
                "taskId": task_id
            },
            "id": request_id
        }
        
        rpc_resp = await self._post_rpc(payload)
        task_data = rpc_resp.result
        return Task(**task_data)

    async def list_tasks(self, limit: int = 10) -> Dict[str, Any]:
        """
        List active tasks.
        Method: tasks/list
        """
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "method": "tasks/list",
            "params": {
                "limit": limit
            },
            "id": request_id
        }
        
        rpc_resp = await self._post_rpc(payload)
        return rpc_resp.result

    async def _post_rpc(self, payload: Dict[str, Any]) -> JsonRpcResponse:
        """Helper to send JSON-RPC POST request."""
        url = f"{self.agent_url}/a2a"  # Assumes standard path, or should be config
        # Note: Some agents might use root, but DKMES uses /a2a. 
        # Ideally agent_url shouldn't include path, but let's assume agent_url is base.
        # If agent_url ends in /a2a, we handle it?
        # Standard: agent_url is the host root. endpoint is defined by spec (usually /a2a or check agent card).
        # For this implementation, we append /a2a if not present or passed.
        
        # NOTE: DKMES backend mounts at /a2a.
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, json=payload, headers=self.headers)
                resp.raise_for_status()
                data = resp.json()
                
                # Parse response
                # Note: JsonRpcResponse model validation might fail if result is generic dict vs strict model
                # We used strict model in a2a.py, let's just return object wrapper
                
                if "error" in data and data["error"]:
                    raise Exception(f"A2A Error {data['error'].get('code')}: {data['error'].get('message')}")
                
                return JsonRpcResponse(**data)
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"RPC Call Failed: {e}")
                raise

    async def ask_and_wait(self, question: str, poll_interval: float = 1.0, max_retries: int = 30) -> str:
        """
        Convenience method: Send message, poll until done, return answer text.
        """
        # 1. Send
        msg = {
            "role": "user",
            "parts": [{"text": question}]
        }
        task = await self.send_message(msg)
        logger.info(f"Task started: {task.id}")
        
        # 2. Poll
        for _ in range(max_retries):
            await asyncio.sleep(poll_interval)
            task = await self.get_task(task.id)
            
            if task.status.state == TaskState.COMPLETED:
                # Extract answer
                if task.status.message and task.status.message.parts:
                    return task.status.message.parts[0].text
                return "Task completed but returned no content."
            
            if task.status.state == TaskState.FAILED:
                error = "Task failed."
                if task.status.message and task.status.message.parts:
                    error += f" Reason: {task.status.message.parts[0].text}"
                return error
        
        # 3. Timeout
        return "Task timed out waiting for response."
