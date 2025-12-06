"""
Tool Calling Framework for Agentic AI System.

This module provides a registry and execution engine for tools that can be
called by the LLM agent autonomously.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class ToolCategory(Enum):
    """Categories of tools available to the agent."""
    RETRIEVAL = "retrieval"
    COMPUTATION = "computation"
    UTILITY = "utility"
    EXTERNAL = "external"


@dataclass
class ToolParameter:
    """Definition of a tool parameter."""
    name: str
    type: str  # "string", "number", "boolean", "array", "object"
    description: str
    required: bool = True
    enum: Optional[List[str]] = None
    default: Optional[Any] = None


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class Tool:
    """
    Represents a tool that can be called by the agent.
    
    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description (used in prompt)
        category: Category of the tool
        parameters: List of parameters the tool accepts
        execute_fn: The actual function to execute
    """
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter]
    execute_fn: Callable[..., Any]
    
    def to_gemini_schema(self) -> Dict[str, Any]:
        """Convert tool definition to Gemini Function Calling schema."""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop
            
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        import time
        start = time.time()
        
        try:
            # Handle both async and sync functions
            result = self.execute_fn(**kwargs)
            if hasattr(result, '__await__'):
                result = await result
            
            execution_time = (time.time() - start) * 1000
            return ToolResult(
                success=True,
                data=result,
                execution_time_ms=execution_time
            )
        except Exception as e:
            execution_time = (time.time() - start) * 1000
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time_ms=execution_time
            )


class ToolRegistry:
    """
    Central registry for all available tools.
    
    The agent queries this registry to know what tools are available
    and how to call them.
    """
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[Tool]:
        """List all tools, optionally filtered by category."""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools
    
    def get_gemini_tools_schema(self) -> List[Dict[str, Any]]:
        """Get all tools in Gemini Function Calling format."""
        return [tool.to_gemini_schema() for tool in self._tools.values()]
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{name}' not found"
            )
        return await tool.execute(**kwargs)


# Global registry instance
_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _registry


def register_tool(
    name: str,
    description: str,
    category: ToolCategory = ToolCategory.UTILITY,
    parameters: Optional[List[ToolParameter]] = None
):
    """
    Decorator to register a function as a tool.
    
    Usage:
        @register_tool(
            name="search_documents",
            description="Search for documents in the knowledge base",
            category=ToolCategory.RETRIEVAL,
            parameters=[
                ToolParameter("query", "string", "The search query"),
                ToolParameter("limit", "number", "Max results", required=False, default=5)
            ]
        )
        async def search_documents(query: str, limit: int = 5):
            ...
    """
    def decorator(fn: Callable) -> Callable:
        tool = Tool(
            name=name,
            description=description,
            category=category,
            parameters=parameters or [],
            execute_fn=fn
        )
        _registry.register(tool)
        return fn
    return decorator


# ============================================================================
# Built-in Tools
# ============================================================================

    try:
        provider = VectorProvider()
        # Use 'top_k' as expected by VectorProvider.search signature
        # Note: VectorProvider.search(query, top_k=5)
        # We need to await it because VectorProvider.search is async defined as 'async def search'
        import asyncio
        # Wait, inside tool execution context, we are already async. 
        # But VectorProvider.search is defined as 'async def'.
        # We should enable awaiting if the tool registry supports async execution.
        # tools.py 'execute_tool' uses 'await' if execute_fn is async.
        # But here 'search_vector' is defined as synchronous 'def search_vector'.
        # We must change 'search_vector' to 'async def search_vector' to await the provider.
        
        # Checking search_vector definition... it was 'def search_vector'. Use 'async def'.
        # Wait, if I change the signature here I must update the decorator usage too? No, registry handles it.
        pass
        
    except Exception as e:
        return {"error": str(e), "documents": [], "count": 0}

# Start Re-definition
@register_tool(
    name="search_vector",
    description="Search for relevant documents using semantic vector similarity. Use this when you need to find documents related to a topic or question.",
    category=ToolCategory.RETRIEVAL,
    parameters=[
        ToolParameter("query", "string", "The search query or question"),
        ToolParameter("num_results", "number", "Number of results to return (1-10)", required=False)
    ]
)
async def search_vector(query: str, num_results: int = 5, **kwargs) -> Dict[str, Any]:
    """Search documents using vector similarity."""
    from knowledge.vector_provider import VectorProvider
    
    if 'top_k' in kwargs:
        num_results = kwargs['top_k']
    
    try:
        provider = VectorProvider()
        results = await provider.search(query, top_k=min(num_results, 5)) # Limit max to 5
        
        # Truncate content to avoid huge context
        for doc in results:
            if "content" in doc and isinstance(doc["content"], str):
                 if len(doc["content"]) > 1000:
                     doc["content"] = doc["content"][:1000] + "...(truncated)"
                     
        return {
            "documents": results,
            "count": len(results)
        }
    except Exception as e:
        return {"error": str(e), "documents": [], "count": 0}


@register_tool(
    name="query_graph",
    description="Query the knowledge graph to find entities and their relationships. Use this when you need structured information about specific entities or connections between concepts.",
    category=ToolCategory.RETRIEVAL,
    parameters=[
        ToolParameter("entity", "string", "The entity name to search for"),
        ToolParameter("relationship_type", "string", "Type of relationship to explore (e.g., 'RELATED_TO', 'MENTIONS')", required=False)
    ]
)
def query_graph(entity: str, relationship_type: str = None) -> Dict[str, Any]:
    """Query the knowledge graph for entities and relationships."""
    from knowledge.graph_provider import GraphProvider
    
    try:
        provider = GraphProvider()
        
        # Build Cypher query
        if relationship_type:
            query = f"""
            MATCH (n)-[r:{relationship_type}]-(m)
            WHERE n.name CONTAINS $entity OR n.id CONTAINS $entity
            RETURN n, r, m LIMIT 10
            """
        else:
            query = """
            MATCH (n)-[r]-(m)
            WHERE n.name CONTAINS $entity OR n.id CONTAINS $entity
            RETURN n, r, m LIMIT 10
            """
        
        results = provider.query(query, {"entity": entity})
        return {
            "entities": results,
            "count": len(results)
        }
    except Exception as e:
        return {"error": str(e), "entities": [], "count": 0}


@register_tool(
    name="get_current_time",
    description="Get the current date and time. Use this when the user asks about the current time or date.",
    category=ToolCategory.UTILITY,
    parameters=[]
)
def get_current_time() -> Dict[str, str]:
    """Get current date and time."""
    from datetime import datetime
    now = datetime.now()
    return {
        "datetime": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day_of_week": now.strftime("%A")
    }


@register_tool(
    name="calculate",
    description="Perform mathematical calculations. Use this for any arithmetic or mathematical operations.",
    category=ToolCategory.COMPUTATION,
    parameters=[
        ToolParameter("expression", "string", "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', '100 * 0.15')")
    ]
)
def calculate(expression: str) -> Dict[str, Any]:
    """Safely evaluate a mathematical expression."""
    import math
    
    # Safe evaluation with limited scope
    allowed_names = {
        'abs': abs, 'round': round, 'min': min, 'max': max,
        'sum': sum, 'pow': pow,
        'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos,
        'tan': math.tan, 'log': math.log, 'log10': math.log10,
        'pi': math.pi, 'e': math.e
    }
    
    try:
        # Remove potentially dangerous characters
        safe_expr = expression.replace("__", "")
        result = eval(safe_expr, {"__builtins__": {}}, allowed_names)
        return {
            "expression": expression,
            "result": result
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e)
        }


@register_tool(
    name="summarize_context",
    description="Provide a summary of retrieved information from both vector and graph sources. Use this after retrieving documents to give a concise overview.",
    category=ToolCategory.UTILITY,
    parameters=[
        ToolParameter("topic", "string", "The topic to summarize"),
        ToolParameter("max_length", "number", "Maximum length of summary in words", required=False)
    ]
)
def summarize_context(topic: str, max_length: int = 100) -> Dict[str, Any]:
    """Summarize retrieved context about a topic."""
    # This will use the LLM to summarize
    # For now, return a placeholder
    return {
        "topic": topic,
        "summary": f"Summary of '{topic}' will be generated using the LLM.",
        "sources_used": 0
    }


# ============================================================================
# Phase 13: Agentic RAG Tools
# ============================================================================

@register_tool(
    name="analyze_query",
    description="Analyze query to determine type, complexity, and domains. Returns analysis for strategy selection.",
    category=ToolCategory.RETRIEVAL,
    parameters=[
        ToolParameter("query", "string", "The user's question or query to analyze")
    ]
)
def analyze_query(query: str, **kwargs) -> Dict[str, Any]:
    """
    Analyze query to determine type, complexity, and domains.
    
    Returns:
        - query_type: factual, conceptual, procedural, comparative
        - complexity: simple, medium, complex
        - domains: list of detected domains
        - entities: key entities mentioned
        - suggested_strategies: recommended retrieval strategies
    """
    query_lower = query.lower()
    
    # Detect query type
    if any(w in query_lower for w in ["what is", "what are", "define", "who is", "when"]):
        query_type = "factual"
    elif any(w in query_lower for w in ["how does", "why", "explain", "concept"]):
        query_type = "conceptual"
    elif any(w in query_lower for w in ["how to", "steps", "process", "guide", "implement"]):
        query_type = "procedural"
    elif any(w in query_lower for w in ["compare", "difference", "vs", "versus", "better"]):
        query_type = "comparative"
    else:
        query_type = "general"
    
    # Detect domains
    domains = []
    domain_keywords = {
        "knowledge-management": ["knowledge", "document", "information", "retrieval", "search"],
        "machine-learning": ["ml", "machine learning", "neural", "model", "training", "deep learning"],
        "artificial-intelligence": ["ai", "artificial intelligence", "agent", "llm", "gpt"],
        "data-science": ["data", "analytics", "statistics", "visualization"]
    }
    
    for domain, keywords in domain_keywords.items():
        if any(kw in query_lower for kw in keywords):
            domains.append(domain)
    
    # Estimate complexity
    word_count = len(query.split())
    has_multiple_parts = " and " in query_lower or "," in query
    
    if word_count > 20 or has_multiple_parts:
        complexity = "complex"
    elif word_count > 10:
        complexity = "medium"
    else:
        complexity = "simple"
    
    # Suggest strategies based on analysis
    suggested_strategies = []
    if query_type in ["factual", "general"]:
        suggested_strategies.append("vector")
    if query_type in ["conceptual", "comparative"]:
        suggested_strategies.append("graph")
    if complexity == "complex":
        suggested_strategies.append("hybrid")
    if any(d in domains for d in ["machine-learning", "artificial-intelligence"]):
        suggested_strategies.append("cross-agent")
    
    return {
        "query_type": query_type,
        "complexity": complexity,
        "domains": domains if domains else ["general"],
        "word_count": word_count,
        "suggested_strategies": suggested_strategies or ["vector"],
        "analysis_complete": True
    }


@register_tool(
    name="select_strategy",
    description="Select the optimal retrieval strategy based on query analysis. Use this after analyze_query.",
    category=ToolCategory.RETRIEVAL,
    parameters=[
        ToolParameter("query_type", "string", "Type of query: factual, conceptual, procedural, comparative, general"),
        ToolParameter("complexity", "string", "Query complexity: simple, medium, complex"),
        ToolParameter("domains", "array", "List of relevant domains"),
        ToolParameter("suggested_strategies", "array", "Optional list of pre-suggested strategies from analysis")
    ]
)
def select_strategy(query_type: str = "general", complexity: str = "simple", domains: list = None, suggested_strategies: list = None, **kwargs) -> Dict[str, Any]:
    """
    Select optimal retrieval strategy.
    
    Strategies:
    - vector: Fast semantic search, good for factual queries
    - graph: Relationship-based, good for conceptual queries  
    - hybrid: Both vector + graph, good for complex queries
    - cross-agent: Query external agents for specialized domains
    """
    strategy_scores = {
        "vector": 0.5,
        "graph": 0.3,
        "hybrid": 0.2,
        "cross-agent": 0.0
    }
    
    # Adjust scores based on query type
    if query_type == "factual":
        strategy_scores["vector"] += 0.3
    elif query_type == "conceptual":
        strategy_scores["graph"] += 0.3
    elif query_type == "procedural":
        strategy_scores["vector"] += 0.2
        strategy_scores["hybrid"] += 0.1
    elif query_type == "comparative":
        strategy_scores["graph"] += 0.2
        strategy_scores["hybrid"] += 0.2
    
    # Adjust for complexity
    if complexity == "complex":
        strategy_scores["hybrid"] += 0.3
        strategy_scores["cross-agent"] += 0.1
    elif complexity == "medium":
        strategy_scores["hybrid"] += 0.1
    
    # Adjust for domains
    external_domains = ["machine-learning", "artificial-intelligence"]
    if any(d in domains for d in external_domains):
        strategy_scores["cross-agent"] += 0.4
    
    # Select best strategy
    best_strategy = max(strategy_scores, key=strategy_scores.get)
    
    return {
        "selected_strategy": best_strategy,
        "strategy_scores": strategy_scores,
        "rationale": f"Selected '{best_strategy}' based on {query_type} query type and {complexity} complexity",
        "fallback_strategy": "hybrid" if best_strategy != "hybrid" else "vector"
    }


@register_tool(
    name="evaluate_context",
    description="Evaluate if the retrieved context is sufficient to answer the query. Use this after retrieval.",
    category=ToolCategory.UTILITY,
    parameters=[
        ToolParameter("query", "string", "The original query"),
        ToolParameter("context_count", "number", "Number of context chunks retrieved"),
        ToolParameter("avg_relevance", "number", "Average relevance score (0-1)")
    ]
)
def evaluate_context(query: str, context_count: int, avg_relevance: float) -> Dict[str, Any]:
    """
    Evaluate if retrieved context is sufficient.
    
    Returns recommendation on whether to proceed or refine query.
    """
    is_sufficient = context_count >= 2 and avg_relevance >= 0.5
    
    if context_count == 0:
        recommendation = "no_results"
        action = "Try different keywords or broader query"
    elif avg_relevance < 0.3:
        recommendation = "low_relevance"
        action = "Refine query to be more specific"
    elif context_count < 2:
        recommendation = "few_results"
        action = "Try hybrid strategy or cross-agent"
    else:
        recommendation = "sufficient"
        action = "Proceed to answer generation"
    
    return {
        "is_sufficient": is_sufficient,
        "recommendation": recommendation,
        "action": action,
        "context_count": context_count,
        "avg_relevance": avg_relevance,
        "quality_score": min(1.0, (context_count / 5) * 0.5 + avg_relevance * 0.5)
    }


@register_tool(
    name="refine_query",
    description="Refine the query to improve retrieval results. Use when context is insufficient.",
    category=ToolCategory.UTILITY,
    parameters=[
        ToolParameter("original_query", "string", "The original query"),
        ToolParameter("issue", "string", "The issue: no_results, low_relevance, few_results")
    ]
)
def refine_query(original_query: str, issue: str) -> Dict[str, Any]:
    """
    Suggest refined queries based on the issue.
    """
    words = original_query.split()
    
    if issue == "no_results":
        # Broaden the query
        refined = " ".join(words[:min(5, len(words))])  # Use fewer words
        suggestion = "Use broader terms"
    elif issue == "low_relevance":
        # Make more specific
        refined = original_query + " definition explanation"
        suggestion = "Add context words"
    else:
        # Try rephrasing
        refined = "explain " + original_query if not original_query.startswith("explain") else original_query
        suggestion = "Rephrase as explanation"
    
    return {
        "original_query": original_query,
        "refined_query": refined,
        "suggestion": suggestion,
        "issue_addressed": issue
    }


@register_tool(
    name="ask_peer_agent",
    description="Request knowledge from a specialized peer agent via A2A protocol. Use for ML/AI topics or when local knowledge is insufficient.",
    category=ToolCategory.EXTERNAL,
    parameters=[
        ToolParameter("query", "string", "The query to send to peer agent"),
        ToolParameter("domain", "string", "Target domain: machine-learning, artificial-intelligence")
    ]
)
async def ask_peer_agent(query: str, domain: str) -> Dict[str, Any]:
    """
    Request knowledge from peer agent via A2A Protocol.
    """
    from core.a2a_client import A2AClient
    
    # Simple registry (in real app, this would be dynamic or config-based)
    peer_urls = {
        "machine-learning": "http://localhost:8001",
        "artificial-intelligence": "http://localhost:8001",
        "ai-ml": "http://localhost:8001"
    }
    
    # Fallback to localhost:8000 (itself) if testing, but ideally 8001
    peer_url = peer_urls.get(domain, "http://localhost:8001")
    
    try:
        client = A2AClient(agent_url=peer_url)
        answer = await client.ask_and_wait(query)
        
        return {
            "success": True,
            "answer": answer,
            "peer_agent": peer_url,
            "protocol": "A2A"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to reach peer agent at {peer_url}: {str(e)}",
            "protocol": "A2A"
        }



@register_tool(
    name="hybrid_search",
    description="Perform combined vector and graph search for comprehensive results. Best for complex queries.",
    category=ToolCategory.RETRIEVAL,
    parameters=[
        ToolParameter("query", "string", "The search query"),
        ToolParameter("vector_weight", "number", "Weight for vector results (0-1)", required=False),
        ToolParameter("max_results", "number", "Maximum total results", required=False)
    ]
)
async def hybrid_search(query: str, vector_weight: float = 0.6, max_results: int = 5) -> Dict[str, Any]:
    """
    Combined vector + graph search.
    """
    from knowledge.vector_provider import VectorProvider
    from knowledge.graph_provider import GraphProvider
    
    vector_results = []
    graph_results = []
    
    try:
        # Vector search
        vector_provider = VectorProvider(persist_directory="./data/chroma")
        vec_res = await vector_provider.search(query, top_k=max_results)
        vector_results = [
            {"source": "vector", "content": r.get("content", "")[:200], "score": r.get("score", 0)}
            for r in vec_res
        ]
    except Exception as e:
        vector_results = [{"error": str(e)}]
    
    try:
        # Graph search - extract entities first
        words = query.split()
        entities_found = []
        graph_provider = GraphProvider(host="localhost", port=6379)
        
        # Search for key terms in graph
        for word in words[:3]:  # Limit to first 3 words
            if len(word) > 3:  # Skip short words
                graph_res = await graph_provider.search(word)
                if graph_res:
                    graph_results.extend([
                        {"source": "graph", "content": str(r)[:200], "score": 0.7}
                        for r in graph_res[:2]
                    ])
    except Exception as e:
        graph_results = [{"error": str(e)}]
    
    # Combine and weight results
    combined = []
    for r in vector_results:
        if "error" not in r:
            r["weighted_score"] = r.get("score", 0) * vector_weight
            combined.append(r)
    
    graph_weight = 1 - vector_weight
    for r in graph_results:
        if "error" not in r:
            r["weighted_score"] = r.get("score", 0) * graph_weight
            combined.append(r)
    
    # Sort by weighted score
    combined.sort(key=lambda x: x.get("weighted_score", 0), reverse=True)
    
    return {
        "results": combined[:max_results],
        "vector_count": len([r for r in vector_results if "error" not in r]),
        "graph_count": len([r for r in graph_results if "error" not in r]),
        "total_count": len(combined),
        "strategy": "hybrid"
    }
