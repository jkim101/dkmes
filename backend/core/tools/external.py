from typing import Dict, Any
from core.tools.base import register_tool, ToolCategory, ToolParameter
from core.a2a_client import A2AClient

@register_tool(
    name="ask_peer_agent",
    description="Request knowledge from a specialized peer agent via A2A protocol.",
    category=ToolCategory.EXTERNAL,
    parameters=[
        ToolParameter("query", "string", "The query to send to peer agent"),
        ToolParameter("domain", "string", "Target domain: machine-learning, artificial-intelligence")
    ]
)
async def ask_peer_agent(query: str, domain: str, **kwargs) -> Dict[str, Any]:
    """Request knowledge from peer agent via A2A Protocol."""
    
    # Simple registry (In production, use config or service discovery)
    peer_urls = {
        "machine-learning": "http://localhost:8001",
        "artificial-intelligence": "http://localhost:8001",
        "ai-ml": "http://localhost:8001"
    }
    
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
