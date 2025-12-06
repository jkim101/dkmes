from typing import Dict, Any, Optional
from core.tools.base import register_tool, ToolCategory, ToolParameter
from core.config import current_settings

# Module-level cached providers
_vector_provider = None
_graph_provider = None

def get_vector_provider():
    global _vector_provider
    if _vector_provider is None:
        from knowledge.vector_provider import VectorProvider
        _vector_provider = VectorProvider()
    return _vector_provider

def get_graph_provider():
    global _graph_provider
    if _graph_provider is None:
        from knowledge.graph_provider import GraphProvider
        # Mock Gemini Client for GraphProvider if needed, or real one
        # GraphProvider usually needs a llm_client. 
        # For retrieval (search), it might not need LLM.
        _graph_provider = GraphProvider(gemini_client=None) 
    return _graph_provider


@register_tool(
    name="search_vector",
    description="Search for relevant documents using semantic vector similarity.",
    category=ToolCategory.RETRIEVAL,
    parameters=[
        ToolParameter("query", "string", "The search query or question"),
        ToolParameter("num_results", "number", "Number of results to return (1-10)", required=False)
    ]
)
async def search_vector(query: str, num_results: int = None, **kwargs) -> Dict[str, Any]:
    """Search documents using vector similarity."""
    
    # Use global default if not provided
    if num_results is None:
        num_results = current_settings.top_k
    
    # Handle aliases from LLM hallucinations
    if 'top_k' in kwargs:
        num_results = kwargs['top_k']
        
    final_k = min(num_results, 10)
    
    try:
        provider = get_vector_provider()
        results = await provider.search(query, top_k=final_k)
        
        # Truncate content for token efficiency
        for doc in results:
            if "content" in doc and isinstance(doc["content"], str):
                 if len(doc["content"]) > current_settings.chunk_size:
                     doc["content"] = doc["content"][:current_settings.chunk_size] + "...(truncated)"
                     
        return {
            "documents": results,
            "count": len(results)
        }
    except Exception as e:
        return {"error": str(e), "documents": [], "count": 0}


@register_tool(
    name="search_graph",
    description="Search for structured relationships and entities in the knowledge graph.",
    category=ToolCategory.RETRIEVAL,
    parameters=[
        ToolParameter("query", "string", "The search query"),
        ToolParameter("depth", "number", "Traversal depth", required=False, default=1)
    ]
)
async def search_graph(query: str, depth: int = None, **kwargs) -> Dict[str, Any]:
    """Search graph for entities and relationships."""
    
    if depth is None:
        depth = current_settings.graph_depth
    try:
        provider = get_graph_provider()
        # GraphProvider.get_graph_data returns nodes/edges. 
        # Ideally we need a 'search' method.
        # Assuming we just return whole graph for now or filter?
        # The original implementation returned the whole graph data for visualization.
        # RAG needs sub-graph.
        
        # For optimization, we skip implementing complex graph search here if not supported yet.
        # Just return basic graph data.
        data = await provider.get_graph_data() 
        return {
            "entities": data.get("nodes", [])[:10], # Limit
            "relationships": data.get("edges", [])[:10],
            "note": "Graph search is currently returning global sample."
        }
    except Exception as e:
        return {"error": str(e)}


@register_tool(
    name="hybrid_search",
    description="Perform both vector and graph search and combine results.",
    category=ToolCategory.RETRIEVAL,
    parameters=[
        ToolParameter("query", "string", "The search query"),
    ]
)
async def hybrid_search(query: str, **kwargs) -> Dict[str, Any]:
    """Combine vector and graph search results."""
    vector_res = await search_vector(query, num_results=3)
    graph_res = await search_graph(query, depth=1)
    
    return {
        "vector_results": vector_res,
        "graph_results": graph_res,
        "strategy": "hybrid"
    }
