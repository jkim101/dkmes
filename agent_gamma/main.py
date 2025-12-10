"""
Agent Gamma - Data Analytics Agent

A Google ADK-style agent for data analytics domain.
Runs on port 8002 and integrates with DKMES Multi-Agent Orchestrator.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import sys
import uuid
import httpx
from datetime import datetime

# =============================================================================
# Configuration
# =============================================================================

AGENT_ID = "agent-gamma-analytics"
AGENT_NAME = "CVDT Chatbot Agent"
AGENT_DOMAIN = "data-analytics"
PORT = 8002
PEER_AGENTS = [
    "http://localhost:8000",  # DKMES Alpha
    "http://localhost:8001",  # Agent Beta
]


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title=f"Agent Gamma - {AGENT_NAME}",
    description="Data Analytics Agent for multi-agent knowledge exchange",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for UI
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# =============================================================================
# Models
# =============================================================================

class HealthResponse(BaseModel):
    status: str
    agent_id: str
    agent_name: str
    domain: str
    timestamp: str


class ChatRequest(BaseModel):
    message: str
    history: List[Dict] = []


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict] = []
    confidence: float = 0.0


class AgentInfo(BaseModel):
    agent_id: str
    name: str
    callback_url: str
    domains: List[str] = []


class KEPRequest(BaseModel):
    request_id: str
    sender_agent_id: str
    query: str
    domain: Optional[str] = None
    context: Dict = {}


class KEPResponse(BaseModel):
    request_id: str
    responder_agent_id: str
    answer: str
    confidence: float
    sources: List[Dict] = []
    metadata: Dict = {}


# =============================================================================
# In-memory storage
# =============================================================================

registered_agents: Dict[str, AgentInfo] = {}
exchange_history: List[Dict] = []


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Redirect to chat UI."""
    return RedirectResponse(url="/static/index.html")


@app.get("/api/info")
async def api_info():
    """API info endpoint."""
    return {
        "agent_id": AGENT_ID,
        "name": AGENT_NAME,
        "domain": AGENT_DOMAIN,
        "port": PORT,
        "peer_agents": PEER_AGENTS,
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint - REQUIRED for Orchestrator integration."""
    return HealthResponse(
        status="healthy",
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        domain=AGENT_DOMAIN,
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Simple chat endpoint."""
    # Mock response for data analytics queries
    answer = f"[{AGENT_NAME}] Analyzing your query: '{request.message}'. " \
             f"This is a mock response. Implement actual analytics logic here."
    
    return ChatResponse(
        answer=answer,
        sources=[],
        confidence=0.75
    )


class AskAlphaRequest(BaseModel):
    message: str


@app.post("/api/v1/ask-alpha")
async def ask_alpha(request: AskAlphaRequest):
    """Forward question to DKMES Alpha via A2A protocol."""
    alpha_a2a_url = "http://localhost:8000/a2a"
    request_id = str(uuid.uuid4())
    
    try:
        # Log the outgoing request
        exchange_history.append({
            "request_id": request_id,
            "sender_agent_id": AGENT_ID,
            "receiver_agent_id": "dkmes-alpha",
            "query": request.message,
            "protocol": "A2A",
            "timestamp": datetime.now().isoformat(),
            "direction": "outgoing"
        })
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Send A2A JSON-RPC request to Alpha
            response = await client.post(
                alpha_a2a_url,
                json={
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "message/send",
                    "params": {
                        "message": {
                            "role": "ROLE_USER",
                            "parts": [{"text": request.message}]
                        }
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                status = result.get("status", {})
                
                # Extract answer from status.message.parts
                answer_text = "No answer received"
                if status.get("message"):
                    parts = status["message"].get("parts", [])
                    if parts and parts[0].get("text"):
                        answer_text = parts[0]["text"]
                
                return {
                    "answer": answer_text,
                    "status": status.get("state", "UNKNOWN"),
                    "task_id": result.get("id"),
                    "from_agent": "dkmes-alpha",
                    "protocol": "A2A"
                }
            else:
                return {
                    "answer": f"Alpha returned error: {response.status_code}",
                    "error": True
                }
                
    except httpx.TimeoutException:
        return {"answer": "Request to Alpha timed out", "error": True}
    except httpx.ConnectError:
        return {"answer": "Cannot connect to DKMES Alpha. Is it running on port 8000?", "error": True}
    except Exception as e:
        return {"answer": f"Error: {str(e)}", "error": True}


# =============================================================================
# KEP (Knowledge Exchange Protocol) Endpoints
# =============================================================================

@app.post("/api/v1/kep/register")
async def register_agent(agent: AgentInfo):
    """Register an external agent."""
    registered_agents[agent.agent_id] = agent
    print(f"✅ Registered agent: {agent.name} ({agent.agent_id})")
    return {
        "status": "success",
        "message": f"Agent '{agent.name}' registered with {AGENT_NAME}",
        "agent_id": agent.agent_id
    }


@app.get("/api/v1/kep/agents")
async def list_agents():
    """List all registered external agents."""
    return {
        "agents": [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "domains": a.domains,
            }
            for a in registered_agents.values()
        ]
    }


@app.post("/api/v1/kep/request", response_model=KEPResponse)
async def process_kep_request(request: KEPRequest):
    """Process a knowledge exchange request from another agent."""
    # Log the exchange
    exchange_history.append({
        "request_id": request.request_id,
        "sender_agent_id": request.sender_agent_id,
        "receiver_agent_id": AGENT_ID,
        "query": request.query,
        "domain": request.domain,
        "timestamp": datetime.now().isoformat(),
        "confidence": 0.8
    })
    
    # Mock analytics response
    answer = f"Data analytics insight for: {request.query}"
    
    return KEPResponse(
        request_id=request.request_id,
        responder_agent_id=AGENT_ID,
        answer=answer,
        confidence=0.8,
        sources=[],
        metadata={"domain": AGENT_DOMAIN}
    )


@app.get("/api/v1/kep/history")
async def get_exchange_history(agent_id: Optional[str] = None, limit: int = 50):
    """Get history of knowledge exchanges."""
    history = exchange_history
    if agent_id:
        history = [h for h in history if h.get("sender_agent_id") == agent_id]
    return {"exchanges": history[-limit:]}


# =============================================================================
# Startup Event
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Register with peer agents on startup."""
    import httpx
    
    print(f"\n{'='*60}")
    print(f"  🚀 {AGENT_NAME} starting on port {PORT}")
    print(f"  Agent ID: {AGENT_ID}")
    print(f"  Domain: {AGENT_DOMAIN}")
    print(f"{'='*60}\n")
    
    # Try to register with peer agents
    for peer_url in PEER_AGENTS:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{peer_url}/api/v1/kep/register",
                    json={
                        "agent_id": AGENT_ID,
                        "name": AGENT_NAME,
                        "callback_url": f"http://localhost:{PORT}/api/v1/kep/feedback",
                        "domains": [AGENT_DOMAIN, "sql-analysis", "data-visualization"]
                    },
                    timeout=5.0
                )
                if response.status_code == 200:
                    print(f"✅ Registered with peer agent at {peer_url}")
                else:
                    print(f"⚠️ Failed to register with {peer_url}: {response.text}")
        except Exception as e:
            print(f"⚠️ Peer agent at {peer_url} not available: {e}")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
