from typing import Literal
from core.gemini_client import GeminiClient

class QueryRouter:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client

    async def route(self, query: str) -> Literal["vector", "graph", "hybrid"]:
        """
        Determines the best retrieval strategy for a given query.
        """
        query_lower = query.lower()
        
        # 1. Heuristic Rules (Fast & Cheap)
        # Graph-heavy keywords
        if any(w in query_lower for w in ["relationship", "connection", "between", "compare", "difference", "summary", "overview", "how are"]):
            return "graph"
        
        # Vector-heavy keywords (Specific facts)
        if any(w in query_lower for w in ["what is", "define", "who", "when", "where", "code for"]):
            return "vector"

        # 2. LLM-based Classification (Fallback for ambiguity)
        # For now, default to Hybrid for maximum coverage if ambiguous
        return "hybrid"

        # Future: Uncomment to use LLM for routing
        # prompt = f"Classify this query into 'vector' (fact lookup), 'graph' (relationship/summary), or 'hybrid' (complex): {query}"
        # response = await self.gemini_client.generate(prompt)
        # return response.strip().lower()
