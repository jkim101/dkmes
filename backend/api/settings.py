from fastapi import APIRouter, HTTPException
from core.config import SystemSettings, current_settings

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

@router.get("", response_model=SystemSettings)
async def get_settings():
    return current_settings

@router.put("", response_model=SystemSettings)
async def update_settings(settings: SystemSettings):
    global current_settings
    # Update global settings
    current_settings.llm_model = settings.llm_model
    current_settings.temperature = settings.temperature
    current_settings.max_output_tokens = settings.max_output_tokens
    current_settings.rag_strategy = settings.rag_strategy
    current_settings.top_k = settings.top_k
    current_settings.chunk_size = settings.chunk_size
    current_settings.chunk_overlap = settings.chunk_overlap
    current_settings.graph_depth = settings.graph_depth
    current_settings.system_prompt_override = settings.system_prompt_override
    
    return current_settings
