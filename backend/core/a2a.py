from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# ============================================================================
# A2A Data Models (Agent Card)
# ============================================================================

class A2AInterface(BaseModel):
    url: str
    protocolBinding: str  # "JSONRPC", "HTTP+JSON", "GRPC"

class A2AProvider(BaseModel):
    organization: str
    url: Optional[str] = None

class A2ASkill(BaseModel):
    id: str
    name: str
    description: str
    tags: List[str] = []
    inputModes: List[str] = ["text/plain"]
    outputModes: List[str] = ["text/plain"]
    examples: List[str] = []

class AgentCard(BaseModel):
    protocolVersion: str = "0.3.0"
    name: str
    description: str
    version: str = "1.0.0"
    supportedInterfaces: List[A2AInterface]
    provider: A2AProvider
    skills: List[A2ASkill]
    capabilities: Dict[str, bool] = {
        "streaming": False,
        "pushNotifications": False,
        "stateTransitionHistory": True
    }

# ============================================================================
# DKMES Agent Card Configuration
# ============================================================================

dkmes_agent_card = AgentCard(
    name="DKMES Alpha",
    description="Data Knowledge Management Eco-System Agent. Specializes in RAG (Retrieval Augmented Generation) over document collections and knowledge graphs.",
    version="1.0.0",
    supportedInterfaces=[
        A2AInterface(url="/a2a", protocolBinding="JSONRPC")
    ],
    provider=A2AProvider(
        organization="Antigravity Team",
        url="https://github.com/jkim101/dkmes"
    ),
    skills=[
        A2ASkill(
            id="knowledge-query",
            name="Knowledge Query",
            description="Answer diverse questions using Vector Search, Graph RAG, or Hybrid strategies.",
            tags=["knowledge", "search", "rag", "graph"],
            examples=[
                "What is the SECI model?",
                "How does machine learning improve knowledge management?"
            ]
        ),
        A2ASkill(
            id="document-analysis",
            name="Document Analysis",
            description="Analyze uploaded documents and extract key insights and relationships.",
            tags=["analysis", "nlp", "extraction"],
            examples=[
                "Summarize the key points of the uploaded PDF.",
                "Extract entities and relationships from this text."
            ]
        )
    ]
)



# ============================================================================
# A2A Core Objects (Task, Message)
# ============================================================================

class TaskState(str):
    UNSPECIFIED = "TASK_STATE_UNSPECIFIED"
    SUBMITTED = "TASK_STATE_SUBMITTED"
    WORKING = "TASK_STATE_WORKING"
    COMPLETED = "TASK_STATE_COMPLETED"
    FAILED = "TASK_STATE_FAILED"
    CANCELLED = "TASK_STATE_CANCELLED"
    INPUT_REQUIRED = "TASK_STATE_INPUT_REQUIRED"
    REJECTED = "TASK_STATE_REJECTED"
    AUTH_REQUIRED = "TASK_STATE_AUTH_REQUIRED"

class Role(str):
    UNSPECIFIED = "ROLE_UNSPECIFIED"
    USER = "ROLE_USER"
    AGENT = "ROLE_AGENT"

class Part(BaseModel):
    text: Optional[str] = None
    # file: Optional[FilePart] = None # Implement later if needed
    # data: Optional[DataPart] = None # Implement later if needed
    metadata: Dict[str, Any] = {}

class Message(BaseModel):
    messageId: str = Field(default_factory=lambda: "") # To be generated
    contextId: Optional[str] = None
    taskId: Optional[str] = None
    role: str = Role.USER
    parts: List[Part]
    metadata: Dict[str, Any] = {}
    extensions: Optional[str] = None
    referenceTaskIds: Optional[str] = None

class TaskStatus(BaseModel):
    state: str = TaskState.SUBMITTED
    message: Optional[Message] = None
    timestamp: float # Unix timestamp

class Task(BaseModel):
    id: str
    contextId: Optional[str] = None
    status: TaskStatus
    artifacts: List[Any] = [] # Artifacts not fully defined yet, using list for now
    history: List[Message] = []
    metadata: Dict[str, Any] = {}


# ============================================================================
# JSON-RPC Models
# ============================================================================

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any]
    id: Any

class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Any

class JsonRpcError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

# A2A Specific Errors
A2A_ERRORS = {
    "PARSE_ERROR": {"code": -32700, "message": "Parse error"},
    "INVALID_REQUEST": {"code": -32600, "message": "Invalid Request"},
    "METHOD_NOT_FOUND": {"code": -32601, "message": "Method not found"},
    "INVALID_PARAMS": {"code": -32602, "message": "Invalid params"},
    "INTERNAL_ERROR": {"code": -32603, "message": "Internal error"},
}


# ============================================================================
# A2A Handler
# ============================================================================

import uuid
import time

class A2AHandler:
    """
    Handles A2A protocol operations.
    
    Supports methods:
    - message/send: Send a message and get response
    - tasks/get: Get task status
    - tasks/cancel: Cancel a task
    """
    
    def __init__(self, agent_id: str, process_message_fn):
        """
        Initialize A2A handler.
        
        Args:
            agent_id: This agent's unique identifier
            process_message_fn: Async function(query: str) -> str that processes messages
        """
        self.agent_id = agent_id
        self.process_message_fn = process_message_fn
        self.tasks: Dict[str, Task] = {}
    
    async def handle_request(self, request_data: Dict) -> Dict:
        """
        Handle an incoming A2A JSON-RPC request.
        
        Routes to appropriate method handler.
        """
        try:
            request = JsonRpcRequest(**request_data)
        except Exception as e:
            return JsonRpcResponse(
                id=request_data.get("id", "unknown"),
                error=A2A_ERRORS["INVALID_REQUEST"]
            ).model_dump()
        
        method = request.method
        
        try:
            if method == "message/send":
                result = await self._handle_send_message(request.params)
                return JsonRpcResponse(id=request.id, result=result).model_dump()
            
            elif method == "tasks/get":
                result = await self._handle_get_task(request.params)
                return JsonRpcResponse(id=request.id, result=result).model_dump()
            
            elif method == "tasks/cancel":
                result = await self._handle_cancel_task(request.params)
                return JsonRpcResponse(id=request.id, result=result).model_dump()
            
            else:
                return JsonRpcResponse(
                    id=request.id,
                    error=A2A_ERRORS["METHOD_NOT_FOUND"]
                ).model_dump()
        
        except Exception as e:
            return JsonRpcResponse(
                id=request.id,
                error={"code": -32603, "message": f"Internal error: {str(e)}"}
            ).model_dump()
    
    async def _handle_send_message(self, params: Dict) -> Dict:
        """Handle message/send - process a message and return response."""
        message_data = params.get("message", {})
        parts = message_data.get("parts", [])
        
        # Extract text from message parts
        query_parts = []
        for part in parts:
            if part.get("text"):
                query_parts.append(part["text"])
        
        query = " ".join(query_parts)
        
        # Create task in WORKING state
        task_id = str(uuid.uuid4())
        context_id = params.get("contextId") or str(uuid.uuid4())
        
        task = Task(
            id=task_id,
            contextId=context_id,
            status=TaskStatus(
                state=TaskState.WORKING,
                timestamp=time.time()
            ),
            history=[Message(
                messageId=str(uuid.uuid4()),
                taskId=task_id,
                role=Role.USER,
                parts=[Part(text=query)]
            )],
            metadata=params.get("metadata", {})
        )
        self.tasks[task_id] = task
        
        # Process the message
        try:
            response_text = await self.process_message_fn(query)
            
            # Create response message
            response_message = Message(
                messageId=str(uuid.uuid4()),
                taskId=task_id,
                role=Role.AGENT,
                parts=[Part(text=response_text)]
            )
            
            # Update task to COMPLETED
            task.status = TaskStatus(
                state=TaskState.COMPLETED,
                message=response_message,
                timestamp=time.time()
            )
            task.artifacts = [{"parts": [{"text": response_text}]}]
            task.history.append(response_message)
            
        except Exception as e:
            # Update task to FAILED
            error_message = Message(
                messageId=str(uuid.uuid4()),
                taskId=task_id,
                role=Role.AGENT,
                parts=[Part(text=str(e))]
            )
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=error_message,
                timestamp=time.time()
            )
        
        return task.model_dump()
    
    async def _handle_get_task(self, params: Dict) -> Dict:
        """Handle tasks/get - retrieve task status."""
        task_id = params.get("id")
        if not task_id:
            raise ValueError("Task ID is required")
        
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        return task.model_dump()
    
    async def _handle_cancel_task(self, params: Dict) -> Dict:
        """Handle tasks/cancel - cancel a task."""
        task_id = params.get("id")
        if not task_id:
            raise ValueError("Task ID is required")
        
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        task.status = TaskStatus(
            state=TaskState.CANCELLED,
            timestamp=time.time()
        )
        return task.model_dump()


# ============================================================================
# A2A Client
# ============================================================================

class A2AClient:
    """
    Client for making A2A requests to other agents.
    """
    
    def __init__(self, my_agent_id: str):
        self.my_agent_id = my_agent_id
        self.discovered_agents: Dict[str, AgentCard] = {}
    
    async def discover_agent(self, base_url: str) -> Optional[AgentCard]:
        """Discover an agent by fetching its Agent Card."""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/.well-known/agent.json",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    card = AgentCard(**data)
                    self.discovered_agents[base_url] = card
                    return card
                    
        except Exception as e:
            print(f"Failed to discover agent at {base_url}: {e}")
        
        return None
    
    async def send_message(
        self, 
        agent_url: str, 
        message: str,
        context_id: Optional[str] = None
    ) -> Optional[Task]:
        """Send a message to another agent via A2A."""
        import httpx
        
        request = JsonRpcRequest(
            jsonrpc="2.0",
            id=str(uuid.uuid4()),
            method="message/send",
            params={
                "message": {
                    "role": Role.USER,
                    "parts": [{"text": message}]
                },
                "contextId": context_id
            }
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    agent_url,
                    json=request.model_dump(),
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("error"):
                        print(f"A2A error: {data['error']}")
                        return None
                    
                    result = data.get("result", {})
                    return Task(**result)
                    
        except Exception as e:
            print(f"A2A request failed: {e}")
        
        return None
    
    def get_response_text(self, task: Task) -> str:
        """Extract the text response from a completed task."""
        if task.artifacts:
            for artifact in task.artifacts:
                parts = artifact.get("parts", []) if isinstance(artifact, dict) else []
                for part in parts:
                    text = part.get("text") if isinstance(part, dict) else None
                    if text:
                        return text
        
        # Fallback to status message
        if task.status.message:
            for part in task.status.message.parts:
                if part.text:
                    return part.text
        
        return ""

