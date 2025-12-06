from pydantic import BaseModel
from typing import Optional

class SystemSettings(BaseModel):
    # LLM Settings
    llm_model: str = "gemini-2.0-flash-exp"
    temperature: float = 0.2
    max_output_tokens: int = 8192
    
    # RAG Settings
    rag_strategy: str = "hybrid" # vector, graph, hybrid
    top_k: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Graph Settings
    graph_depth: int = 2
    
    # System Prompts
    system_prompt_override: Optional[str] = None

# Global instance (in-memory persistence for now)
current_settings = SystemSettings()
