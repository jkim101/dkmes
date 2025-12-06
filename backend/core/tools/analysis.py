from typing import Dict, Any, List
from core.tools.base import register_tool, ToolCategory, ToolParameter

@register_tool(
    name="analyze_query",
    description="Analyze the user's query to understand intent, complexity, and key domains.",
    category=ToolCategory.COMPUTATION,
    parameters=[
        ToolParameter("query", "string", "The user's input query")
    ]
)
def analyze_query(query: str, **kwargs) -> Dict[str, Any]:
    """Analyze the query to determine intent and strategy."""
    
    # Keyword analysis (Rule-based for efficiency, avoiding another LLM call)
    query_lower = query.lower()
    
    # 1. Determine Query Type
    if any(w in query_lower for w in ["what", "who", "when", "where"]):
        q_type = "factual"
    elif any(w in query_lower for w in ["how", "why", "explain"]):
        q_type = "explanatory"
    elif any(w in query_lower for w in ["compare", "difference", "vs"]):
        q_type = "comparative"
    else:
        q_type = "general"
        
    # 2. Estimate Complexity
    word_count = len(query.split())
    if word_count > 20 or " and " in query_lower:
        complexity = "complex"
    else:
        complexity = "simple"
        
    # 3. Modify Domains (Taxonomy Mapping)
    domains = []
    if any(w in query_lower for w in ["learn", "training", "education"]):
        domains.append("learning")
    if any(w in query_lower for w in ["code", "python", "java", "api"]):
        domains.append("engineering")
    if any(w in query_lower for w in ["model", "ai", "ml", "network"]):
        domains.append("machine-learning")
        
    return {
        "query_type": q_type,
        "complexity": complexity,
        "domains": domains,
        "word_count": word_count,
        "suggested_strategies": ["vector", "graph"] if complexity == "complex" else ["vector"],
        "analysis_complete": True
    }


@register_tool(
    name="evaluate_context",
    description="Evaluate if the retrieved context is sufficient to answer the query.",
    category=ToolCategory.UTILITY,
    parameters=[
        ToolParameter("query", "string", "The original query"),
        ToolParameter("context_count", "number", "Number of context chunks retrieved"),
        ToolParameter("avg_relevance", "number", "Average relevance score (0-1)")
    ]
)
def evaluate_context(query: str, context_count: int, avg_relevance: float, **kwargs) -> Dict[str, Any]:
    """Evaluate context sufficiency."""
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
        "quality_score": min(1.0, (context_count / 5) * 0.5 + avg_relevance * 0.5)
    }

@register_tool(
    name="refine_query",
    description="Refine the query to improve retrieval results.",
    category=ToolCategory.UTILITY,
    parameters=[
        ToolParameter("original_query", "string", "The original query"),
        ToolParameter("issue", "string", "The issue: no_results, low_relevance, few_results")
    ]
)
def refine_query(original_query: str, issue: str, **kwargs) -> Dict[str, Any]:
    """Suggest refined queries."""
    words = original_query.split()
    
    if issue == "no_results":
        refined = " ".join(words[:min(5, len(words))])
        suggestion = "Use broader terms"
    elif issue == "low_relevance":
        refined = original_query + " definition explanation"
        suggestion = "Add context words"
    else:
        refined = "explain " + original_query if not original_query.lower().startswith("explain") else original_query
        suggestion = "Rephrase as explanation"
    
    return {
        "original_query": original_query,
        "refined_query": refined,
        "suggestion": suggestion
    }
