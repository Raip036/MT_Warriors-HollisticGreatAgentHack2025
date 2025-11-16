"""
Base Tool class for dynamic tool system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Result from a tool execution."""
    success: bool = Field(description="Whether the tool execution succeeded")
    output: Any = Field(description="Output from the tool")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseTool(ABC):
    """
    Base class for all tools in the system.
    All tools must inherit from this and implement the execute method.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with given arguments.
        
        Args:
            **kwargs: Tool-specific arguments
        
        Returns:
            ToolResult with success status, output, and optional error
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get the tool schema for LLM function calling.
        Returns a JSON schema describing the tool's parameters.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }
    
    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for tool parameters.
        Override in subclasses to define parameter structure.
        """
        pass
    
    def validate_args(self, **kwargs) -> bool:
        """
        Validate tool arguments before execution.
        Override in subclasses for custom validation.
        """
        return True

