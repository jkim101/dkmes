from fastapi import APIRouter, HTTPException, Request
from core.a2a import JsonRpcRequest, JsonRpcResponse, A2A_ERRORS
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/a2a")
async def handle_a2a_rpc(request: Request):
    try:
        data = await request.json()
        rpc_req = JsonRpcRequest(**data)
    except Exception as e:
        return JsonRpcResponse(
            id=None,
            error=A2A_ERRORS["PARSE_ERROR"]
        )
    
    # Dispatch methods
    if rpc_req.method == "message/send":
        return await handle_message_send(rpc_req, request)
    elif rpc_req.method == "tasks/get":
        return await handle_task_get(rpc_req)
    elif rpc_req.method == "tasks/list":
        return await handle_task_list(rpc_req)
    else:
        return JsonRpcResponse(
            id=rpc_req.id,
            error=A2A_ERRORS["METHOD_NOT_FOUND"]
        )

from core.task_manager import task_manager
from core.a2a import Message, Part, Role, TaskState
from core.gemini_client import GeminiClient

async def handle_message_send(req: JsonRpcRequest, request: Request) -> JsonRpcResponse:
    params = req.params
    message_data = params.get("message", {})
    context_id = params.get("contextId")

    # 1. Create a new Task
    task = task_manager.create_task(context_id=context_id)
    
    # 2. Store incoming user message
    user_message = Message(**message_data)
    user_message.taskId = task.id
    task_manager.add_message_to_task(task.id, user_message)

    # 3. Update Task to Working
    task_manager.update_task_status(task.id, TaskState.WORKING)

    # 4. Get GeminiClient from app.state
    gemini_client: GeminiClient = request.app.state.gemini_client
    # Note: VectorProvider and GraphProvider are attached to GeminiClient in main.py logic if needed,
    # or GeminiClient is passed to them.
    # Actually, main.py initialized providers:
    # graph_provider(gemini_client=...)
    # But AgenticGeminiClient usually needs tools or access to providers to use them.
    # In Phase 13, tools were registered to a global registry or the client was given access.
    # We should assume tools are already registered in 'backend/core/tools.py'.
    # So using the global 'gemini_client' which is initialized in 'main.py' is sufficient.

    # 5. Async Process
    asyncio.create_task(process_task_background(task.id, user_message, gemini_client))

    # 6. Return Task
    return JsonRpcResponse(
        id=req.id,
        result=task.model_dump()
    )

# Start with task logic
import asyncio
from core.gemini_client import AgentResponse, AgenticGeminiClient, GeminiClient

async def process_task_background(task_id: str, input_message: Message, client: GeminiClient):
    """
    Process the task using AgenticGeminiClient capabilities.
    """
    try:
        # Check if the client supports tools (Agentic capabilities)
        # In main.py, we initialize 'GeminiClient'. We need to upgrade this.
        # But for now, we can check attribute or cast.
        # Ideally, main.py should use AgenticGeminiClient.
        
        # NOTE: If client is base GeminiClient, it won't have 'generate_with_tools'.
        # We'll handle this by checking if it has the method, or temporarily creating an agentic wrapper.
        
        agentic_client = client
        if not hasattr(client, 'generate_with_tools'):
             # Create an AgenticGeminiClient sharing the same config
             agentic_client = AgenticGeminiClient(
                 project_id=client.project_id,
                 location=client.location,
                 model_name=client.model_name
             )
             # Manually copy API key if not in env (though it should be)
             agentic_client.api_key = client.api_key
             if client.is_mock:
                 agentic_client.is_mock = True

        # Extract text input
        input_text = ""
        if input_message.parts:
            input_text = "\n".join([p.text for p in input_message.parts if p.text])
        
        if not input_text:
            raise ValueError("No text input provided")

        # Call Agent
        response: AgentResponse = await agentic_client.generate_with_tools(input_text)
        
        # Prepare Output Message
        output_text = response.answer
        
        # Clean up output text if it looks like JSON structure (sometimes happens if agent fails)
        if output_text.strip().startswith("{") and '"tool":' in output_text:
             output_text = "I attempted to use a tool but encountered a parsing error. However, here is what I found: " + output_text

        if response.reasoning_trace:
            output_text += f"\n\n**Reasoning Trace:**\n{response.reasoning_trace}"
            
        response_message = Message(
            taskId=task_id,
            role=Role.AGENT,
            parts=[Part(text=output_text)],
            metadata={
                "usage": response.usage if hasattr(response, "usage") else {},
                "reasoning_trace": response.reasoning_trace
            }
        )
        
        task_manager.update_task_status(task_id, TaskState.COMPLETED, message=response_message)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_message = Message(
            taskId=task_id,
            role=Role.AGENT,
            parts=[Part(text=f"Error processing task: {str(e)}")],
            metadata={"error": True}
        )
        task_manager.update_task_status(task_id, TaskState.FAILED, message=error_message)



async def handle_task_get(req: JsonRpcRequest) -> JsonRpcResponse:
    task_id = req.params.get("taskId")
    if not task_id:
         return JsonRpcResponse(
            id=req.id,
            error=A2A_ERRORS["INVALID_PARAMS"]
        )
        
    task = task_manager.get_task(task_id)
    if not task:
        return JsonRpcResponse(
             id=req.id,
             error={"code": -32000, "message": "Task not found"}
        )
        
    return JsonRpcResponse(
        id=req.id,
        result=task.model_dump()
    )

async def handle_task_list(req: JsonRpcRequest) -> JsonRpcResponse:
    # Optional: support limit/offset in params
    params = req.params or {}
    limit = params.get("limit", 10)
    tasks = task_manager.list_tasks(limit=limit)
    
    return JsonRpcResponse(
        id=req.id,
        result={"tasks": [t.model_dump() for t in tasks]}
    )
