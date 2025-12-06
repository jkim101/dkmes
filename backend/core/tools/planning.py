from typing import Dict, Any, List, Optional
from core.tools.base import register_tool, ToolCategory, ToolParameter

@register_tool(
    name="select_strategy",
    description="Select the best retrieval strategy based on query analysis.",
    category=ToolCategory.UTILITY,
    parameters=[
        ToolParameter("query_type", "string", "factual, explanatory, comparative"),
        ToolParameter("complexity", "string", "simple, complex"),
        ToolParameter("domains", "array", "List of detected domains", required=False),
        ToolParameter("suggested_strategies", "array", "Strategies suggested by analysis", required=False)
    ]
)
def select_strategy(
    query_type: str, 
    complexity: str, 
    domains: Optional[List[str]] = None,
    suggested_strategies: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Dynamically select RAG strategy."""
    
    if domains is None:
        domains = []
    if suggested_strategies is None:
        suggested_strategies = []
        
    strategy_scores = {
        "vector": 0.5,
        "graph": 0.3,
        "hybrid": 0.4,
        "cross-agent": 0.0
    }
    
    # Heuristics
    if query_type == "factual":
        strategy_scores["vector"] += 0.3
    elif query_type in ["explanatory", "comparative"]:
        strategy_scores["graph"] += 0.3
        strategy_scores["hybrid"] += 0.2
        
    if complexity == "complex":
        strategy_scores["graph"] += 0.2
        strategy_scores["hybrid"] += 0.3
        
    # External domains
    external_domains = ["machine-learning", "artificial-intelligence"]
    if any(d in domains for d in external_domains):
        strategy_scores["cross-agent"] += 0.8  # Strong signal for external
        
    best_strategy = max(strategy_scores, key=strategy_scores.get)
    
    return {
        "selected_strategy": best_strategy,
        "rationale": f"Selected '{best_strategy}' for {query_type}/{complexity} query.",
        "fallback_strategy": "vector"
    }
