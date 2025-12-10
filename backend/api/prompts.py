from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
from core.prompt_manager import PromptManager

router = APIRouter()
prompt_manager = PromptManager()

class PromptUpdate(BaseModel):
    content: str

@router.get("/prompts")
async def list_prompts():
    """List all available system prompts."""
    return prompt_manager.list_prompts()

@router.get("/prompts/{name}")
async def get_prompt(name: str):
    """Get a specific prompt template."""
    content = prompt_manager.get_template(name)
    if not content:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"name": name, "content": content}

@router.put("/prompts/{name}")
async def update_prompt(name: str, update: PromptUpdate):
    """Update a prompt template."""
    prompt_manager.update_template(name, update.content)
    return {"status": "success", "name": name}
