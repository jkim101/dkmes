"""
Tool Calling Framework Base Layer.

This module provides the core data structures and registry for the tool system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import asyncio

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
