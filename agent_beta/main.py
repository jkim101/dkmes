"""
Agent Beta - AI/ML Research Agent

A second Gemini-based agent for testing bidirectional knowledge exchange.
Runs on port 8001 with a different domain (AI/ML Research).
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import sys
import time
from datetime import datetime

# Add parent directory to path for shared modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from core.kep import KEPHandler, KEPRequest, KEPResponse, KEPFeedback, AgentInfo
from core.feedback import get_feedback_store, get_feedback_aggregator
from core.assessment import SelfAssessmentEngine

# Import providers
from knowledge.vector_provider import VectorProvider
from knowledge.graph_provider import GraphProvider
from core.gemini_client import GeminiClient


# =============================================================================
# Configuration
# =============================================================================

AGENT_ID = "agent-beta-aiml"
AGENT_NAME = "AI/ML Research Agent"
AGENT_DOMAIN = "artificial-intelligence"
PORT = 8001
PEER_AGENT_URL = "http://localhost:8000"  # Agent Alpha (DKMES)


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title=f"Agent Beta - {AGENT_NAME}",
    description="AI/ML Research Agent for bidirectional knowledge exchange",
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


# =============================================================================
# Initialize Providers
# =============================================================================

# Use separate data directories for Agent Beta
BETA_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
BETA_CHROMA_DIR = os.path.join(BETA_DATA_DIR, "chroma_beta")
BETA_KEP_DB = os.path.join(BETA_DATA_DIR, "kep_beta.db")
BETA_FEEDBACK_DB = os.path.join(BETA_DATA_DIR, "feedback_beta.db")
BETA_ASSESSMENT_DB = os.path.join(BETA_DATA_DIR, "assessment_beta.db")

# Create directories
os.makedirs(BETA_CHROMA_DIR, exist_ok=True)

# Initialize providers
vector_provider = VectorProvider(
    collection_name="agent_beta_docs",
    persist_directory=BETA_CHROMA_DIR
)
graph_provider = GraphProvider()  # Shared graph for now
gemini_client = GeminiClient()

# KEP Handler with Beta-specific database
kep_handler = KEPHandler(
    vector_provider=vector_provider,
    graph_provider=graph_provider,
    gemini_client=gemini_client,
    db_path=BETA_KEP_DB
)


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


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint with agent info."""
    return {
        "agent_id": AGENT_ID,
        "name": AGENT_NAME,
        "domain": AGENT_DOMAIN,
        "port": PORT,
        "peer_agent": PEER_AGENT_URL,
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        agent_id=AGENT_ID,
        agent_name=AGENT_NAME,
        domain=AGENT_DOMAIN,
        timestamp=datetime.now().isoformat()
    )


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Simple chat endpoint using local knowledge."""
    try:
        # Search local vector store
        results = await vector_provider.search(request.message, top_k=5)
        
        # Build context
        context_parts = []
        sources = []
        for i, doc in enumerate(results):
            content = doc.get("content", "")
            context_parts.append(content)
            sources.append({
                "id": f"src_{i}",
                "excerpt": content[:200] + "..." if len(content) > 200 else content,
                "score": doc.get("score", 0.0)
            })
        
        context = "\n\n".join(context_parts)
        
        # Generate answer
        answer = await gemini_client.generate_answer(
            query=request.message,
            context=context
        )
        
        # Calculate confidence
        avg_score = sum(s["score"] for s in sources) / len(sources) if sources else 0.0
        confidence = 1.0 - min(avg_score, 1.0)  # Lower distance = higher confidence
        
        return ChatResponse(
            answer=answer,
            sources=sources,
            confidence=confidence
        )
    except Exception as e:
        return ChatResponse(
            answer=f"Error: {str(e)}",
            sources=[],
            confidence=0.0
        )


# =============================================================================
# KEP Endpoints (Same as Agent Alpha)
# =============================================================================

@app.post("/api/v1/kep/register")
async def register_agent(agent: AgentInfo):
    """Register an external agent."""
    success = kep_handler.register_agent(agent)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to register agent")
    return {
        "status": "success",
        "message": f"Agent '{agent.name}' registered with {AGENT_NAME}",
        "agent_id": agent.agent_id
    }


@app.get("/api/v1/kep/agents")
async def list_agents():
    """List all registered external agents."""
    agents = kep_handler.list_agents()
    return {
        "agents": [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "domains": a.domains,
                "registered_at": a.registered_at.isoformat(),
                "last_active": a.last_active.isoformat() if a.last_active else None
            }
            for a in agents
        ]
    }


@app.post("/api/v1/kep/request", response_model=KEPResponse)
async def process_kep_request(request: KEPRequest):
    """Process a knowledge exchange request."""
    response = await kep_handler.process_request(request)
    return response


@app.get("/api/v1/kep/history")
async def get_exchange_history(agent_id: Optional[str] = None, limit: int = 50):
    """Get history of knowledge exchanges."""
    history = kep_handler.get_exchange_history(agent_id=agent_id, limit=limit)
    return {"exchanges": history}


@app.post("/api/v1/kep/feedback")
async def receive_feedback(feedback: KEPFeedback):
    """Receive feedback from external agents."""
    store = get_feedback_store()
    feedback_id = store.store_feedback(feedback)
    return {
        "status": "success",
        "message": "Feedback received",
        "feedback_id": feedback_id
    }


# =============================================================================
# Assessment Endpoints
# =============================================================================

assessment_engine = SelfAssessmentEngine(
    vector_provider=vector_provider,
    graph_provider=graph_provider,
    kep_handler=kep_handler,
    db_path=BETA_ASSESSMENT_DB
)


@app.post("/api/v1/assessment/run")
async def run_assessment(domain: Optional[str] = None):
    """Run self-assessment."""
    report = await assessment_engine.run_assessment(domain=domain)
    return {
        "timestamp": report.timestamp,
        "domain": report.domain,
        "overall_score": report.overall_score,
        "dimensions": report.dimensions,
        "recommendations": report.recommendations
    }


# =============================================================================
# Startup Event
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Register with peer agent on startup."""
    import httpx
    
    print(f"\n{'='*60}")
    print(f"  {AGENT_NAME} starting on port {PORT}")
    print(f"  Agent ID: {AGENT_ID}")
    print(f"  Domain: {AGENT_DOMAIN}")
    print(f"{'='*60}\n")
    
    # Try to register with peer agent
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PEER_AGENT_URL}/api/v1/kep/register",
                json={
                    "agent_id": AGENT_ID,
                    "name": AGENT_NAME,
                    "callback_url": f"http://localhost:{PORT}/api/v1/kep/feedback",
                    "domains": [AGENT_DOMAIN, "machine-learning", "deep-learning"]
                },
                timeout=5.0
            )
            if response.status_code == 200:
                print(f"✅ Registered with peer agent at {PEER_AGENT_URL}")
            else:
                print(f"⚠️ Failed to register with peer agent: {response.text}")
    except Exception as e:
        print(f"⚠️ Peer agent not available: {e}")
        print("   Will retry when peer comes online.")


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
