"""
Tool Manager for dynamic tool registration and execution
"""

import time
from typing import Dict, Optional, List, Any
from .base_tool import BaseTool, ToolResult


class ToolManager:
    """
    Manages tool registration, discovery, and execution with full traceability.
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.tool_call_history: List[Dict] = []
    
    def register_tool(self, tool: BaseTool):
        """
        Register a tool for use by the agent.
        
        Args:
            tool: Instance of BaseTool to register
        """
        if not isinstance(tool, BaseTool):
            raise ValueError(f"Tool must be an instance of BaseTool, got {type(tool)}")
        
        self.tools[tool.name] = tool
        print(f"✅ Registered tool: {tool.name} - {tool.description}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a registered tool by name."""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of all registered tools with their schemas."""
        return [tool.get_schema() for tool in self.tools.values()]
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: Optional[str] = None,
        trace_manager=None
    ) -> ToolResult:
        """
        Execute a tool with full traceability.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments to pass to the tool
            session_id: Session ID for tracing
            trace_manager: TraceManager instance for logging
        
        Returns:
            ToolResult from tool execution
        """
        tool = self.get_tool(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}"
            return ToolResult(
                success=False,
                output=None,
                error=error_msg
            )
        
        # Validate arguments
        if not tool.validate_args(**arguments):
            return ToolResult(
                success=False,
                output=None,
                error=f"Invalid arguments for tool '{tool_name}'"
            )
        
        # Log tool call start
        start_time = time.time()
        step_id = None
        
        if trace_manager and session_id:
            step_id = trace_manager.append_tool_call(
                session_id=session_id,
                tool_name=tool_name,
                arguments=arguments,
                output=None,  # Will be updated after execution
                duration_ms=0,  # Will be updated after execution
                success=True,  # Will be updated if error occurs
                metadata={"status": "executing"}
            )
        
        # Execute tool
        try:
            result = await tool.execute(**arguments)
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful tool call
            if trace_manager and session_id:
                trace_manager.append_tool_call(
                    session_id=session_id,
                    tool_name=tool_name,
                    arguments=arguments,
                    output=result.output,
                    duration_ms=duration_ms,
                    success=result.success,
                    error=result.error,
                    metadata={
                        **result.metadata,
                        "duration_ms": duration_ms,
                        "status": "completed"
                    }
                )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            # Log failed tool call
            if trace_manager and session_id:
                trace_manager.append_tool_call(
                    session_id=session_id,
                    tool_name=tool_name,
                    arguments=arguments,
                    output=None,
                    duration_ms=duration_ms,
                    success=False,
                    error=error_msg,
                    metadata={"status": "failed", "exception_type": type(e).__name__}
                )
            
            return ToolResult(
                success=False,
                output=None,
                error=error_msg
            )
    
    def get_tool_schemas_for_llm(self) -> List[Dict[str, Any]]:
        """
        Get tool schemas formatted for LLM function calling.
        """
        return self.list_tools()


# Global singleton instance
_tool_manager_instance: Optional[ToolManager] = None


def get_tool_manager() -> ToolManager:
    """Get the global tool manager instance."""
    global _tool_manager_instance
    if _tool_manager_instance is None:
        _tool_manager_instance = ToolManager()
    return _tool_manager_instance

