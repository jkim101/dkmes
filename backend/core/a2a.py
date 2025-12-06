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
