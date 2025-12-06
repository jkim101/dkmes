"""
Knowledge Exchange Protocol (KEP) Module

A2A-inspired protocol for asynchronous knowledge exchange between agents.
Enables DKMES to share domain-specific knowledge with external agents
and receive federated feedback.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import json


# =============================================================================
# Protocol Models
# =============================================================================

class AgentInfo(BaseModel):
    """Information about a registered external agent."""
    agent_id: str
    name: str
    description: Optional[str] = None
    callback_url: str  # URL for receiving feedback
    domains: List[str] = []  # Domains this agent is interested in
    registered_at: datetime = Field(default_factory=datetime.now)
    last_active: Optional[datetime] = None


class KEPRequest(BaseModel):
    """
    Knowledge Exchange Protocol Request.
    
    Sent by external agents to request knowledge from DKMES.
    """
    protocol_version: str = "1.0"
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_agent_id: str
    domain: str  # Domain of knowledge requested (defined by user metadata)
    query: str  # The question or topic
    context: Dict[str, Any] = {}  # Additional context (user expertise, etc.)
    callback_url: Optional[str] = None  # Override default callback for this request
    priority: str = "normal"  # low, normal, high


class KnowledgeSource(BaseModel):
    """A source document that contributed to the answer."""
    source_id: str
    title: str
    relevance_score: float
    excerpt: str


class KEPResponse(BaseModel):
    """
    Knowledge Exchange Protocol Response.
    
    Returned to external agents with the requested knowledge.
    """
    request_id: str
    protocol_version: str = "1.0"
    status: str = "success"  # success, error, partial
    knowledge: Dict[str, Any] = Field(default_factory=dict)
    # knowledge contains:
    # - answer: str
    # - sources: List[KnowledgeSource]
    # - confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    # metadata contains:
    # - domain: str
    # - knowledge_version: str
    # - processing_time_ms: float
    error: Optional[str] = None


class FeedbackType(str, Enum):
    """Types of feedback that can be received."""
    RATING = "rating"  # Numerical rating (1-5)
    CORRECTION = "correction"  # User corrected the answer
    CONFIRMATION = "confirmation"  # User confirmed answer was correct
    REJECTION = "rejection"  # Answer was not useful


class KEPFeedback(BaseModel):
    """
    Feedback from external agent about knowledge usefulness.
    
    This feedback comes from the external agent's end-users,
    allowing DKMES to assess real-world knowledge quality.
    """
    request_id: str  # Links to original KEPRequest
    sender_agent_id: str
    feedback_type: FeedbackType
    rating: Optional[float] = None  # 1.0 to 5.0
    was_useful: bool = True
    correction: Optional[str] = None  # If user provided correction
    comments: Optional[str] = None
    user_context: Dict[str, Any] = {}  # Domain, expertise level, etc.
    timestamp: datetime = Field(default_factory=datetime.now)


# =============================================================================
# KEP Handler
# =============================================================================

class KEPHandler:
    """
    Handles Knowledge Exchange Protocol operations.
    
    Responsibilities:
    - Process incoming knowledge requests
    - Generate knowledge responses using RAG
    - Manage agent registration
    - Track exchange history
    """
    
    def __init__(self, vector_provider, graph_provider, gemini_client, db_path: str = "kep.db"):
        self.vector_provider = vector_provider
        self.graph_provider = graph_provider
        self.gemini_client = gemini_client
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for KEP data."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Registered agents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                callback_url TEXT,
                domains TEXT,
                registered_at REAL,
                last_active REAL
            )
        """)
        
        # Knowledge exchange history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exchanges (
                request_id TEXT PRIMARY KEY,
                sender_agent_id TEXT,
                domain TEXT,
                query TEXT,
                response TEXT,
                confidence REAL,
                timestamp REAL,
                FOREIGN KEY(sender_agent_id) REFERENCES agents(agent_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def register_agent(self, agent: AgentInfo) -> bool:
        """Register an external agent."""
        import sqlite3
        import time
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO agents 
                (agent_id, name, description, callback_url, domains, registered_at, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                agent.agent_id,
                agent.name,
                agent.description,
                agent.callback_url,
                json.dumps(agent.domains),
                time.time(),
                None
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error registering agent: {e}")
            return False
        finally:
            conn.close()
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent information by ID."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return AgentInfo(
            agent_id=row["agent_id"],
            name=row["name"],
            description=row["description"],
            callback_url=row["callback_url"],
            domains=json.loads(row["domains"]) if row["domains"] else [],
            registered_at=datetime.fromtimestamp(row["registered_at"]),
            last_active=datetime.fromtimestamp(row["last_active"]) if row["last_active"] else None
        )
    
    def list_agents(self) -> List[AgentInfo]:
        """List all registered agents."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM agents ORDER BY registered_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        agents = []
        for row in rows:
            agents.append(AgentInfo(
                agent_id=row["agent_id"],
                name=row["name"],
                description=row["description"],
                callback_url=row["callback_url"],
                domains=json.loads(row["domains"]) if row["domains"] else [],
                registered_at=datetime.fromtimestamp(row["registered_at"]),
                last_active=datetime.fromtimestamp(row["last_active"]) if row["last_active"] else None
            ))
        return agents
    
    async def process_request(self, request: KEPRequest) -> KEPResponse:
        """
        Process a knowledge exchange request.
        
        1. Validate the request
        2. Retrieve relevant knowledge (Vector + Graph)
        3. Generate answer using Gemini
        4. Log the exchange
        5. Return KEPResponse
        """
        import time
        start_time = time.time()
        
        try:
            # 1. Validate sender agent
            agent = self.get_agent(request.sender_agent_id)
            if not agent:
                return KEPResponse(
                    request_id=request.request_id,
                    status="error",
                    error=f"Unknown agent: {request.sender_agent_id}. Please register first."
                )
            
            # 2. Retrieve knowledge using hybrid RAG
            # Vector search
            vector_results = await self.vector_provider.search(request.query, top_k=5)
            
            # Graph search (if available)
            graph_results = []
            try:
                graph_results = await self.graph_provider.search(request.query, limit=5)
            except:
                pass  # Graph may not have relevant data
            
            # Combine context
            context_parts = []
            sources = []
            
            for i, doc in enumerate(vector_results):
                content = doc.get("content", doc.get("text", ""))
                context_parts.append(content)
                sources.append(KnowledgeSource(
                    source_id=f"vec_{i}",
                    title=doc.get("metadata", {}).get("source", f"Document {i+1}"),
                    relevance_score=doc.get("score", 0.0),
                    excerpt=content[:200] + "..." if len(content) > 200 else content
                ))
            
            context = "\n\n".join(context_parts)
            
            # 3. Generate answer
            answer = await self.gemini_client.generate_answer(
                query=request.query,
                context=context
            )
            
            # Calculate confidence based on source relevance
            avg_relevance = sum(s.relevance_score for s in sources) / len(sources) if sources else 0.0
            confidence = min(avg_relevance + 0.2, 1.0)  # Boost slightly
            
            # 4. Log the exchange
            processing_time = (time.time() - start_time) * 1000
            self._log_exchange(request, answer, confidence)
            
            # Update agent's last active time
            self._update_agent_activity(request.sender_agent_id)
            
            # 5. Return response
            return KEPResponse(
                request_id=request.request_id,
                status="success",
                knowledge={
                    "answer": answer,
                    "sources": [s.model_dump() for s in sources],
                    "confidence": confidence
                },
                metadata={
                    "domain": request.domain,
                    "knowledge_version": datetime.now().strftime("%Y-%m-%d"),
                    "processing_time_ms": processing_time,
                    "source_count": len(sources)
                }
            )
            
        except Exception as e:
            return KEPResponse(
                request_id=request.request_id,
                status="error",
                error=str(e)
            )
    
    def _log_exchange(self, request: KEPRequest, answer: str, confidence: float):
        """Log a knowledge exchange to the database."""
        import sqlite3
        import time
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO exchanges 
            (request_id, sender_agent_id, domain, query, response, confidence, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.request_id,
            request.sender_agent_id,
            request.domain,
            request.query,
            answer,
            confidence,
            time.time()
        ))
        
        conn.commit()
        conn.close()
    
    def _update_agent_activity(self, agent_id: str):
        """Update the last_active timestamp for an agent."""
        import sqlite3
        import time
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE agents SET last_active = ? WHERE agent_id = ?",
            (time.time(), agent_id)
        )
        conn.commit()
        conn.close()
    
    def get_exchange_history(self, agent_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get history of knowledge exchanges."""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if agent_id:
            cursor.execute(
                "SELECT * FROM exchanges WHERE sender_agent_id = ? ORDER BY timestamp DESC LIMIT ?",
                (agent_id, limit)
            )
        else:
            cursor.execute(
                "SELECT * FROM exchanges ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "request_id": row["request_id"],
                "sender_agent_id": row["sender_agent_id"],
                "domain": row["domain"],
                "query": row["query"],
                "confidence": row["confidence"],
                "timestamp": datetime.fromtimestamp(row["timestamp"]).isoformat()
            }
            for row in rows
        ]


# =============================================================================
# KEP Client (Outgoing Requests)
# =============================================================================

class KEPClient:
    """
    Client for making outgoing knowledge requests to other agents.
    
    Enables this agent to:
    1. Discover and register with peer agents
    2. Request knowledge from peer agents
    3. Handle responses and integrate external knowledge
    """
    
    def __init__(self, my_agent_id: str, my_agent_name: str, my_callback_url: str, my_domains: List[str]):
        self.my_agent_id = my_agent_id
        self.my_agent_name = my_agent_name
        self.my_callback_url = my_callback_url
        self.my_domains = my_domains
        self.peer_agents: Dict[str, Dict] = {}  # agent_id -> {url, domains, ...}
    
    def register_peer(self, agent_id: str, agent_url: str, domains: List[str] = []):
        """Register a peer agent that we can request knowledge from."""
        self.peer_agents[agent_id] = {
            "url": agent_url,
            "domains": domains,
            "registered_at": datetime.now().isoformat()
        }
        print(f"📝 Registered peer agent: {agent_id} at {agent_url}")
    
    def get_peer_for_domain(self, domain: str) -> Optional[str]:
        """Find a peer agent that handles the given domain."""
        for agent_id, info in self.peer_agents.items():
            if domain in info.get("domains", []):
                return agent_id
        return None
    
    async def register_with_peer(self, peer_url: str) -> bool:
        """Register ourselves with a peer agent."""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{peer_url}/api/v1/kep/register",
                    json={
                        "agent_id": self.my_agent_id,
                        "name": self.my_agent_name,
                        "callback_url": self.my_callback_url,
                        "domains": self.my_domains
                    },
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Failed to register with peer: {e}")
            return False
    
    async def request_knowledge(
        self, 
        peer_url: str, 
        query: str, 
        domain: str,
        context: Dict[str, Any] = {}
    ) -> Optional[KEPResponse]:
        """
        Request knowledge from a peer agent.
        
        Args:
            peer_url: Base URL of the peer agent
            query: The question to ask
            domain: Domain of the query
            context: Additional context
            
        Returns:
            KEPResponse if successful, None if failed
        """
        import httpx
        
        request = KEPRequest(
            sender_agent_id=self.my_agent_id,
            domain=domain,
            query=query,
            context=context,
            callback_url=self.my_callback_url
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{peer_url}/api/v1/kep/request",
                    json=request.model_dump(),
                    timeout=30.0  # Longer timeout for knowledge requests
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return KEPResponse(**data)
                else:
                    print(f"KEP request failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"KEP request error: {e}")
            return None
    
    async def request_from_best_peer(
        self, 
        query: str, 
        domain: str,
        context: Dict[str, Any] = {}
    ) -> Optional[KEPResponse]:
        """
        Find the best peer for a domain and request knowledge.
        
        Returns None if no suitable peer is found.
        """
        # Find peer that handles this domain
        for agent_id, info in self.peer_agents.items():
            peer_domains = info.get("domains", [])
            if domain in peer_domains or any(d in domain for d in peer_domains):
                return await self.request_knowledge(
                    peer_url=info["url"],
                    query=query,
                    domain=domain,
                    context=context
                )
        
        # Try first available peer as fallback
        if self.peer_agents:
            first_peer = list(self.peer_agents.values())[0]
            return await self.request_knowledge(
                peer_url=first_peer["url"],
                query=query,
                domain=domain,
                context=context
            )
        
        return None
    
    async def send_feedback(
        self, 
        peer_url: str, 
        request_id: str, 
        rating: float,
        was_useful: bool,
        comments: Optional[str] = None
    ) -> bool:
        """Send feedback to a peer about their knowledge response."""
        import httpx
        
        feedback = KEPFeedback(
            request_id=request_id,
            sender_agent_id=self.my_agent_id,
            feedback_type=FeedbackType.RATING,
            rating=rating,
            was_useful=was_useful,
            comments=comments,
            user_context={"sender_domains": self.my_domains}
        )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{peer_url}/api/v1/kep/feedback",
                    json=feedback.model_dump(),
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Failed to send feedback: {e}")
            return False

