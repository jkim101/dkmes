from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import time
from dotenv import load_dotenv
import io

# Text Extraction Libraries
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup

from core.gemini_client import GeminiClient
from knowledge.graph_provider import GraphProvider
from knowledge.vector_provider import VectorProvider

load_dotenv(".env.local")

from fastapi.middleware.cors import CORSMiddleware

from api import documents, a2a

app = FastAPI(title="DKMES API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(documents.router, prefix="/api/v1/documents")
app.include_router(a2a.router)  # No prefix for /a2a as per A2A spec


# Initialize Clients
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
gemini_client = GeminiClient(project_id=PROJECT_ID)

# Initialize Knowledge Providers
graph_provider = GraphProvider(host="localhost", port=6379, gemini_client=gemini_client)
vector_provider = VectorProvider(persist_directory="./data/chroma")

# Store in app.state for access in routers
app.state.gemini_client = gemini_client
app.state.vector_provider = vector_provider
app.state.graph_provider = graph_provider

from core.tracer import TraceLogger
tracer = TraceLogger()

class IngestRequest(BaseModel):
    text: str

class EvaluationRequest(BaseModel):
    query: str
    agent_id: str
    persona: str = "Novice"

class EvaluationResult(BaseModel):
    score: float
    feedback: str
    context: list
    debug_info: dict
    metrics: Dict[str, float] = {}

def calculate_rouge_l(candidate: str, reference: str) -> float:
    """
    Simple ROUGE-L implementation (Longest Common Subsequence).
    """
    if not candidate or not reference:
        return 0.0
        
    c_tokens = candidate.split()
    r_tokens = reference.split()
    
    m = len(c_tokens)
    n = len(r_tokens)
    
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if c_tokens[i-1] == r_tokens[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
                
    lcs = dp[m][n]
    
    if lcs == 0:
        return 0.0
        
    precision = lcs / m
    recall = lcs / n
    
    if precision + recall == 0:
        return 0.0
        
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1

class ComparisonResponse(BaseModel):
    vector: EvaluationResult
    graph: EvaluationResult
    hybrid: EvaluationResult

@app.get("/")
def read_root():
    return {"message": "Welcome to DKMES (Data Knowledge Management Eco-System)"}


@app.get("/health")
def health_check():
    """Health check endpoint for orchestrator status monitoring."""
    return {
        "status": "online",
        "agent_id": "dkmes-alpha",
        "domain": "knowledge-management",
        "port": 8000
    }

from core.a2a import dkmes_agent_card

@app.get("/.well-known/agent.json")
def get_agent_card():
    """
    Returns the A2A Agent Card for discovery.
    """
    # Create absolute URL for the interface if needed, but relative usually works if client resolves it.
    # For stricter compliance, we might need full URLs, but we'll start with path.
    return dkmes_agent_card.model_dump()

# ... (Ingest endpoints remain same) ...

@app.post("/api/v1/evaluate", response_model=ComparisonResponse)
async def evaluate_agent(request: EvaluationRequest):
    """
    Evaluate agent using Vector, Graph, and Hybrid methods side-by-side.
    """
    start_time = time.time()
    trace_id = tracer.start_trace(request.query, metadata={"agent_id": request.agent_id, "persona": request.persona})
    
    try:
        # 1. Retrieve Contexts
        tracer.log_step(trace_id, "Retrieval Start", request.query, "Starting retrieval for all strategies")
        
        # Graph Search
        graph_search_result = await graph_provider.search(request.query)
        graph_context_text = graph_search_result.get("text_results", [])
        graph_data = graph_search_result.get("graph_data", {"nodes": [], "links": []})
        tracer.log_step(trace_id, "Graph Retrieval", request.query, graph_context_text, metadata={"node_count": len(graph_data['nodes'])})
        
        # Vector Search
        vector_context = await vector_provider.search(request.query)
        tracer.log_step(trace_id, "Vector Retrieval", request.query, [r['content'][:50]+"..." for r in vector_context], metadata={"count": len(vector_context)})
        
        # Format Contexts
        formatted_graph = graph_context_text
        formatted_vector = [f"Doc: {r['content']} (Score: {r['score']:.2f})" for r in vector_context]
        
        # Hybrid is Union (Simple Merge for now)
        formatted_hybrid = list(set(formatted_graph + formatted_vector))
        
        async def evaluate_single_strategy(context, strategy_name, extra_debug_info=None):
            try:
                tracer.log_step(trace_id, f"LLM Judge Start ({strategy_name})", {"context_len": len(context)}, "Sending to Gemini")
                
                # 1. Generate Answer for this strategy (needed for RAGAS)
                context_str = "\n".join(context)
                system_answer = await gemini_client.generate_answer(request.query, context_str)
                
                # 2. Main LLM Judge (Overall Score)
                judge_response_str = await gemini_client.evaluate_rag_context(request.query, context, request.persona)
                judge_response_str = judge_response_str.replace("```json", "").replace("```", "").strip()
                judge_result = json.loads(judge_response_str)
                
                # 3. Calculate Advanced Metrics
                # RAGAS (LLM-based)
                faithfulness = await gemini_client.calculate_faithfulness(request.query, system_answer, context)
                relevance = await gemini_client.calculate_answer_relevance(request.query, system_answer)
                # Context Recall needs Ground Truth, which we don't have in this live eval mode, so we skip or mock it.
                # For now, let's assume no ground truth available in live mode.
                
                metrics = {
                    "faithfulness": faithfulness,
                    "answer_relevance": relevance,
                    "rouge_l": 0.0 # No ground truth in live eval
                }
                
                tracer.log_step(trace_id, f"LLM Judge End ({strategy_name})", "Gemini Response", judge_result)
                
                debug_info = {
                    "strategy": strategy_name,
                    "raw_judge_response": judge_result,
                    "generated_answer": system_answer
                }
                if extra_debug_info:
                    debug_info.update(extra_debug_info)
                
                return EvaluationResult(
                    score=judge_result.get("score", 0.0),
                    feedback=judge_result.get("reasoning", "No reasoning provided"),
                    context=context,
                    debug_info=debug_info,
                    metrics=metrics
                )
            except Exception as e:
                print(f"Judge Error ({strategy_name}): {e}")
                tracer.log_step(trace_id, f"Error ({strategy_name})", str(e), "Failed")
                return EvaluationResult(
                    score=0.0,
                    feedback=f"Evaluation failed: {str(e)}",
                    context=context,
                    debug_info={"error": str(e)},
                    metrics={}
                )

        # 2. Run Evaluations (could be parallelized with asyncio.gather)
        vector_eval = await evaluate_single_strategy(formatted_vector, "Vector")
        graph_eval = await evaluate_single_strategy(formatted_graph, "Graph", extra_debug_info={"graph_data": graph_data})
        hybrid_eval = await evaluate_single_strategy(formatted_hybrid, "Hybrid")

        response = ComparisonResponse(
            vector=vector_eval,
            graph=graph_eval,
            hybrid=hybrid_eval
        )
        
        tracer.end_trace(trace_id, status="success", latency=time.time() - start_time)
        return response

    except Exception as e:
        tracer.end_trace(trace_id, status="error", latency=time.time() - start_time)
        tracer.log_step(trace_id, "Fatal Error", str(e), "Trace Failed")
        raise e

class BatchPair(BaseModel):
    question: str
    ground_truth: str
    
    class Config:
        extra = "allow"  # Allow additional fields like id, category, difficulty

class BatchEvaluationRequest(BaseModel):
    pairs: List[BatchPair]

@app.post("/api/v1/batch-evaluate")
async def batch_evaluate(request: BatchEvaluationRequest):
    """
    Run batch evaluation on a list of Q&A pairs.
    """
    results = []
    total_score = 0
    
    for pair in request.pairs:
        # For batch, we'll default to Hybrid for simplicity, or we could run all.
        # Let's run Hybrid as the "System" strategy for now to save time/cost, 
        # or we can iterate all. The UI expects a list of "BatchResult".
        
        # Re-using evaluate_agent logic but simplified for batch
        # We need to call evaluate_agent internally or refactor logic.
        # To avoid code duplication, let's call the internal logic.
        
        # Construct a single evaluation request
        single_req = EvaluationRequest(query=pair.question, agent_id="batch-runner", persona="Expert")
        
        try:
            # Call the existing evaluate function (we need to await it)
            # Note: This calls the route handler directly which is fine in FastAPI but 
            # better to extract logic. For speed, we'll call it.
            comparison = await evaluate_agent(single_req)
            
            # Process all three strategies: Vector, Graph, Hybrid
            strategies = [
                ("Vector", comparison.vector),
                ("Graph", comparison.graph),
                ("Hybrid", comparison.hybrid)
            ]
            
            for strategy_name, strategy_res in strategies:
                system_answer = strategy_res.debug_info.get("generated_answer", "N/A")
                
                # Calculate ROUGE-L for text similarity
                rouge_score = calculate_rouge_l(system_answer, pair.ground_truth)
                
                # Get RAGAS metrics from evaluation
                metrics = strategy_res.metrics if strategy_res.metrics else {}
                faithfulness = metrics.get("faithfulness", 0.0)
                relevance = metrics.get("answer_relevance", 0.0)
                
                # Calculate overall score as average of all metrics
                overall_score = (rouge_score + faithfulness + relevance) / 3.0
                
                results.append({
                    "question": pair.question,
                    "ground_truth": pair.ground_truth,
                    "system_answer": system_answer,
                    "strategy": strategy_name,
                    "metrics": {
                        "rouge_l": rouge_score,
                        "faithfulness": faithfulness,
                        "answer_relevance": relevance,
                        "overall": overall_score
                    }
                })
                total_score += overall_score
            
        except Exception as e:
            print(f"Batch Item Error: {e}")
            results.append({
                "question": pair.question,
                "ground_truth": pair.ground_truth,
                "system_answer": "Error",
                "strategy": "Hybrid",
                "metrics": {
                    "rouge_l": 0.0,
                    "faithfulness": 0.0,
                    "answer_relevance": 0.0,
                    "overall": 0.0
                }
            })

    avg_score = total_score / len(request.pairs) if request.pairs else 0
    
    return {
        "results": results,
        "average_score": avg_score
    }

@app.get("/api/v1/graph/visualize")
async def visualize_graph():
    data = await graph_provider.get_graph_data(limit=500)
    return data

class NodeUpdate(BaseModel):
    properties: Dict[str, Any]

@app.put("/api/v1/graph/nodes/{node_id}")
async def update_node(node_id: str, update: NodeUpdate):
    success = await graph_provider.update_node(node_id, update.properties)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update node")
    return {"status": "success"}

@app.delete("/api/v1/graph/nodes/{node_id}")
async def delete_node(node_id: str):
    success = await graph_provider.delete_node(node_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete node")
    return {"status": "success"}

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    strategy: str = "Hybrid"  # Options: Vector, Graph, Hybrid

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint with selectable RAG strategy.
    """
    start_time = time.time()
    trace_id = tracer.start_trace(request.message, metadata={"type": "chat", "strategy": request.strategy})
    
    try:
        # 1. Retrieve Context based on Strategy
        tracer.log_step(trace_id, "Retrieval Start", request.message, f"Fetching context using {request.strategy}")
        
        context = []
        vector_context = []
        graph_context = []

        # Vector Search
        if request.strategy in ["Vector", "Hybrid"]:
            vector_results = await vector_provider.search(request.message)
            vector_context = [r['content'] for r in vector_results]
            tracer.log_step(trace_id, "Vector Retrieval", request.message, [c[:50]+"..." for c in vector_context])

        # Graph Search
        if request.strategy in ["Graph", "Hybrid"]:
            graph_results = await graph_provider.search(request.message)
            graph_context = graph_results.get("text_results", [])
            tracer.log_step(trace_id, "Graph Retrieval", request.message, graph_context)
        
        # Combine
        context = list(set(vector_context + graph_context))
        tracer.log_step(trace_id, "Context Combined", {"vector_count": len(vector_context), "graph_count": len(graph_context)}, context)
        
        # 2. Generate Answer
        tracer.log_step(trace_id, "Generation Start", "Sending to Gemini", "...")
        answer = await gemini_client.generate_answer(request.message, "\n".join(context))
        tracer.log_step(trace_id, "Generation End", "Gemini Response", answer)
        
        tracer.end_trace(trace_id, status="success", latency=time.time() - start_time)
        
        return {
            "answer": answer,
            "context": context,
            "strategy": request.strategy,
            "trace_id": trace_id
        }
    except Exception as e:
        tracer.end_trace(trace_id, status="error", latency=time.time() - start_time)
        tracer.log_step(trace_id, "Fatal Error", str(e), "Trace Failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/stats")
async def get_system_stats():
    """
    Get system statistics and status.
    """
    try:
        # Get Graph Stats
        graph_stats = await graph_provider.get_stats()
        
        # Get Vector Stats
        vector_stats = await vector_provider.get_stats()
        
        return {
            "status": "online",
            "vector_chunks": vector_stats.get("vector_chunks", 0),
            "graph_nodes": graph_stats.get("graph_nodes", 0),
            "graph_edges": graph_stats.get("graph_edges", 0)
        }
    except Exception as e:
        print(f"Error getting system stats: {e}")
        return {
            "status": "offline",
            "vector_chunks": 0,
            "graph_nodes": 0,
            "graph_edges": 0
        }


# ============================================================================
# Trace API Endpoints (for Inspector UI)
# ============================================================================

@app.get("/api/v1/traces")
async def get_traces(limit: int = 50):
    """Get recent traces for the Inspector UI."""
    traces = tracer.get_recent_traces(limit=limit)
    return traces


@app.get("/api/v1/traces/{trace_id}")
async def get_trace_detail(trace_id: str):
    """Get detailed trace information including all steps."""
    detail = tracer.get_trace_details(trace_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Trace not found")
    return detail


# ============================================================================
# Phase 11: Agentic AI Endpoints
# ============================================================================

from core.gemini_client import AgenticGeminiClient, AgentResponse, ToolCall

# Initialize Agentic Client
agentic_client = AgenticGeminiClient(project_id=PROJECT_ID)


class AgentChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []
    use_tools: bool = True


class AgentChatResponse(BaseModel):
    answer: str
    tool_calls: List[Dict[str, Any]] = []
    thinking: str = ""
    reasoning_trace: str = ""


@app.post("/api/v1/agent/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest):
    """
    Agentic chat endpoint with autonomous tool calling.
    
    The agent can decide to use tools (search, query graph, calculate, etc.)
    to gather information before answering.
    """
    start_time = time.time()
    trace_id = tracer.start_trace(
        query=request.message, 
        metadata={"trace_type": "agent_chat"}
    )
    
    try:
        tracer.log_step(trace_id, "Agent Request", request.message, "Processing")
        
        # Build context from history
        history_context = ""
        if request.history:
            for msg in request.history[-5:]:  # Last 5 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_context += f"{role}: {content}\n"
        
        # Call agentic client
        if request.use_tools:
            response = await agentic_client.generate_with_tools(
                query=request.message,
                context=f"Conversation History:\n{history_context}" if history_context else ""
            )
        else:
            # Fallback to regular generation
            answer = await gemini_client.generate_answer(
                query=request.message,
                context=history_context
            )
            response = AgentResponse(answer=answer, tool_calls=[])
        
        # Log tool calls
        for tc in response.tool_calls:
            tracer.log_step(
                trace_id, 
                f"Tool: {tc.name}", 
                str(tc.arguments), 
                f"Result: {str(tc.result)[:100]}..."
            )
        
        tracer.log_step(trace_id, "Agent Response", response.answer[:200], "Complete")
        tracer.end_trace(trace_id, status="success", latency=time.time() - start_time)
        
        return AgentChatResponse(
            answer=response.answer,
            tool_calls=[
                {
                    "name": tc.name,
                    "arguments": tc.arguments,
                    "result": tc.result,
                    "execution_time_ms": tc.execution_time_ms
                }
                for tc in response.tool_calls
            ],
            thinking=response.thinking,
            reasoning_trace=response.reasoning_trace
        )
        
    except Exception as e:
        tracer.end_trace(trace_id, status="error", latency=time.time() - start_time)
        tracer.log_step(trace_id, "Agent Error", str(e), "Failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/agent/tools")
async def list_available_tools():
    """
    List all available tools that the agent can use.
    """
    from core.tools import get_tool_registry
    
    registry = get_tool_registry()
    tools = registry.list_tools()
    
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category.value,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "required": p.required
                    }
                    for p in tool.parameters
                ]
            }
            for tool in tools
        ]
    }


# ============================================================================
# Phase 11.2: Knowledge Exchange Protocol (KEP) Endpoints
# ============================================================================

from core.kep import KEPHandler, KEPRequest, KEPResponse, KEPFeedback, AgentInfo

# Initialize KEP Handler
kep_handler = KEPHandler(
    vector_provider=vector_provider,
    graph_provider=graph_provider,
    gemini_client=gemini_client
)


@app.post("/api/v1/kep/register")
async def register_agent(agent: AgentInfo):
    """
    Register an external agent.
    
    External agents must register before they can request knowledge.
    """
    success = kep_handler.register_agent(agent)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to register agent")
    return {
        "status": "success",
        "message": f"Agent '{agent.name}' registered successfully",
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
    """
    Process a knowledge exchange request from an external agent.
    
    The agent must be registered before making requests.
    """
    response = await kep_handler.process_request(request)
    return response


@app.get("/api/v1/kep/history")
async def get_exchange_history(agent_id: Optional[str] = None, limit: int = 50):
    """Get history of knowledge exchanges."""
    history = kep_handler.get_exchange_history(agent_id=agent_id, limit=limit)
    return {"exchanges": history}


# ============================================================================
# Phase 12.2: Cross-Agent KEP Client
# ============================================================================

from core.kep import KEPClient

# Initialize KEP Client for this agent (Alpha)
kep_client = KEPClient(
    my_agent_id="dkmes-alpha",
    my_agent_name="DKMES Alpha",
    my_callback_url="http://localhost:8000/api/v1/kep/feedback",
    my_domains=["knowledge-management", "domain-knowledge"]
)

# Register known peer agents
kep_client.register_peer(
    agent_id="agent-beta-aiml",
    agent_url="http://localhost:8001",
    domains=["artificial-intelligence", "machine-learning", "deep-learning"]
)


class PeerQueryRequest(BaseModel):
    """Request to query a peer agent."""
    query: str
    domain: str = "general"
    peer_agent_id: Optional[str] = None  # If None, find best peer


class PeerQueryResponse(BaseModel):
    """Response from peer agent query."""
    success: bool
    peer_agent_id: Optional[str] = None
    answer: Optional[str] = None
    sources: List[Dict] = []
    confidence: float = 0.0
    error: Optional[str] = None


@app.post("/api/v1/kep/ask-peer", response_model=PeerQueryResponse)
async def ask_peer_agent(request: PeerQueryRequest):
    """
    Ask a peer agent for knowledge.
    
    Useful when local knowledge is insufficient or when 
    the query falls outside this agent's domain expertise.
    """
    try:
        # Request from best peer for this domain
        response = await kep_client.request_from_best_peer(
            query=request.query,
            domain=request.domain
        )
        
        if response and response.status == "success":
            knowledge = response.knowledge
            return PeerQueryResponse(
                success=True,
                peer_agent_id=response.metadata.get("responding_agent", "unknown"),
                answer=knowledge.get("answer", ""),
                sources=knowledge.get("sources", []),
                confidence=knowledge.get("confidence", 0.0)
            )
        elif response:
            return PeerQueryResponse(
                success=False,
                error=response.error or "Request failed"
            )
        else:
            return PeerQueryResponse(
                success=False,
                error="No peer agent available for this domain"
            )
    except Exception as e:
        return PeerQueryResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/v1/kep/peers")
async def list_peer_agents():
    """List known peer agents that this agent can query."""
    return {
        "peers": [
            {
                "agent_id": agent_id,
                "url": info["url"],
                "domains": info["domains"],
                "registered_at": info["registered_at"]
            }
            for agent_id, info in kep_client.peer_agents.items()
        ]
    }


# ============================================================================
# Phase 12.3: Knowledge Fusion
# ============================================================================

class FusedQueryRequest(BaseModel):
    """Request for fused knowledge from multiple agents."""
    query: str
    use_local: bool = True
    use_peers: bool = True
    peer_domains: List[str] = ["artificial-intelligence", "machine-learning"]


class KnowledgeSource(BaseModel):
    """A source of knowledge from either local or peer agent."""
    agent_id: str
    source_type: str  # "local" or "peer"
    content: str
    confidence: float


class FusedQueryResponse(BaseModel):
    """Response combining knowledge from multiple sources."""
    answer: str
    local_used: bool
    peers_used: List[str] = []
    sources: List[Dict] = []
    combined_confidence: float
    fusion_metadata: Dict = {}


@app.post("/api/v1/chat/fused", response_model=FusedQueryResponse)
async def fused_chat(request: FusedQueryRequest):
    """
    Intelligent chat that fuses local knowledge with peer agent knowledge.
    
    Flow:
    1. Search local knowledge base
    2. Request knowledge from relevant peer agents  
    3. Combine contexts from all sources
    4. Generate a unified answer citing all sources
    """
    start_time = time.time()
    all_context_parts = []
    all_sources = []
    peers_used = []
    local_confidence = 0.0
    peer_confidence = 0.0
    
    # 1. Get local knowledge
    if request.use_local:
        try:
            local_results = await vector_provider.search(request.query, top_k=3)
            
            for i, doc in enumerate(local_results):
                content = doc.get("content", doc.get("text", ""))
                score = doc.get("score", 0.0)
                
                all_context_parts.append(f"[Local Source {i+1}]\n{content}")
                all_sources.append({
                    "agent": "dkmes-alpha",
                    "type": "local",
                    "excerpt": content[:150] + "..." if len(content) > 150 else content,
                    "score": score
                })
                local_confidence = max(local_confidence, 1.0 - min(score, 1.0))
        except Exception as e:
            print(f"Local search error: {e}")
    
    # 2. Get peer knowledge
    if request.use_peers:
        for domain in request.peer_domains:
            try:
                peer_response = await kep_client.request_from_best_peer(
                    query=request.query,
                    domain=domain
                )
                
                if peer_response and peer_response.status == "success":
                    knowledge = peer_response.knowledge
                    answer = knowledge.get("answer", "")
                    sources = knowledge.get("sources", [])
                    conf = knowledge.get("confidence", 0.0)
                    
                    # Add peer knowledge to context
                    if sources:
                        for src in sources[:2]:  # Limit to 2 sources per peer
                            excerpt = src.get("excerpt", "")
                            all_context_parts.append(f"[Peer Agent: {domain}]\n{excerpt}")
                            all_sources.append({
                                "agent": "agent-beta-aiml",
                                "type": "peer",
                                "domain": domain,
                                "excerpt": excerpt[:150] + "..." if len(excerpt) > 150 else excerpt,
                                "score": src.get("relevance_score", 0.5)
                            })
                    
                    peers_used.append(domain)
                    peer_confidence = max(peer_confidence, conf)
                    break  # Only use first matching peer per domain
                    
            except Exception as e:
                print(f"Peer query error for {domain}: {e}")
    
    # 3. Generate fused answer
    combined_context = "\n\n---\n\n".join(all_context_parts)
    
    if combined_context:
        # Create prompt emphasizing source diversity
        fusion_prompt = f"""You are answering a question using knowledge from multiple sources.
        
Sources include:
- Local knowledge base (knowledge management expertise)
- Peer AI agent (machine learning / AI expertise)

Question: {request.query}

Available Context:
{combined_context}

Instructions:
1. Synthesize information from ALL available sources
2. If sources have different perspectives, present both
3. Be accurate and cite which type of source provided each piece of information
4. If knowledge is limited, say so

Answer:"""
        
        answer = await gemini_client.generate_answer(
            query=request.query,
            context=fusion_prompt
        )
    else:
        answer = "No relevant knowledge found from local or peer sources."
    
    # 4. Calculate combined confidence
    if local_confidence > 0 and peer_confidence > 0:
        combined_confidence = (local_confidence * 0.6 + peer_confidence * 0.4)
    elif local_confidence > 0:
        combined_confidence = local_confidence * 0.8
    elif peer_confidence > 0:
        combined_confidence = peer_confidence * 0.8
    else:
        combined_confidence = 0.0
    
    processing_time = (time.time() - start_time) * 1000
    
    return FusedQueryResponse(
        answer=answer,
        local_used=request.use_local and local_confidence > 0,
        peers_used=peers_used,
        sources=all_sources,
        combined_confidence=combined_confidence,
        fusion_metadata={
            "local_confidence": local_confidence,
            "peer_confidence": peer_confidence,
            "processing_time_ms": processing_time,
            "source_count": len(all_sources)
        }
    )



# ============================================================================
# Phase 11.3: Federated Feedback System
# ============================================================================

from core.feedback import (
    FeedbackStore, FeedbackAggregator, FeedbackStats,
    get_feedback_store, get_feedback_aggregator
)
from core.kep import KEPFeedback


@app.post("/api/v1/kep/feedback")
async def receive_feedback(feedback: KEPFeedback):
    """
    Receive feedback from external agents about knowledge usefulness.
    
    This webhook is called by external agents when their end-users
    provide feedback about knowledge received from DKMES.
    """
    store = get_feedback_store()
    feedback_id = store.store_feedback(feedback)
    
    return {
        "status": "success",
        "message": "Feedback received",
        "feedback_id": feedback_id
    }


@app.get("/api/v1/feedback/recent")
async def get_recent_feedback(limit: int = 50):
    """Get recent feedback across all agents."""
    store = get_feedback_store()
    feedback_list = store.get_recent_feedback(limit=limit)
    return {"feedback": feedback_list}


@app.get("/api/v1/feedback/stats")
async def get_feedback_stats(days: int = 30):
    """Get aggregated feedback statistics."""
    aggregator = get_feedback_aggregator()
    
    overall = aggregator.get_overall_stats(days=days)
    by_agent = aggregator.get_stats_by_agent(days=days)
    low_rated = aggregator.get_low_rated_requests(threshold=2.5, limit=10)
    
    return {
        "overall": {
            "total_feedback": overall.total_feedback,
            "avg_rating": overall.avg_rating,
            "useful_rate": overall.useful_rate,
            "correction_rate": overall.correction_rate
        },
        "by_agent": {
            agent_id: {
                "total_feedback": stats.total_feedback,
                "avg_rating": stats.avg_rating,
                "useful_rate": stats.useful_rate
            }
            for agent_id, stats in by_agent.items()
        },
        "low_rated_requests": low_rated,
        "period_days": days
    }


@app.get("/api/v1/feedback/for-request/{request_id}")
async def get_feedback_for_request(request_id: str):
    """Get all feedback for a specific knowledge exchange request."""
    store = get_feedback_store()
    feedback_list = store.get_feedback_for_request(request_id)
    return {"feedback": feedback_list}


# ============================================================================
# Phase 11.4: Self-Assessment Engine
# ============================================================================

from core.assessment import SelfAssessmentEngine, get_assessment_engine, AssessmentReport

# Initialize Assessment Engine with providers
assessment_engine = SelfAssessmentEngine(
    vector_provider=vector_provider,
    graph_provider=graph_provider,
    kep_handler=kep_handler
)


@app.post("/api/v1/assessment/run")
async def run_assessment(domain: Optional[str] = None):
    """
    Trigger a self-assessment of knowledge quality.
    
    Returns a comprehensive report with scores across 4 dimensions:
    - Usefulness (from federated feedback)
    - Coverage (knowledge base completeness)
    - Consistency (internal consistency)
    - Freshness (recency of knowledge)
    """
    report = await assessment_engine.run_assessment(domain=domain)
    
    return {
        "timestamp": report.timestamp,
        "domain": report.domain,
        "overall_score": report.overall_score,
        "dimensions": report.dimensions,
        "dimension_details": [
            {
                "dimension": d.dimension,
                "score": d.score,
                "details": d.details,
                "recommendations": d.recommendations
            }
            for d in report.dimension_details
        ],
        "recommendations": report.recommendations,
        "metadata": report.metadata
    }


@app.get("/api/v1/assessment/history")
async def get_assessment_history(limit: int = 20):
    """Get history of past self-assessments."""
    history = assessment_engine.get_assessment_history(limit=limit)
    return {"assessments": history}


@app.get("/api/v1/assessment/trend")
async def get_assessment_trend(days: int = 30):
    """Get score trend over time."""
    trend = assessment_engine.get_score_trend(days=days)
    return {"trend": trend, "period_days": days}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



