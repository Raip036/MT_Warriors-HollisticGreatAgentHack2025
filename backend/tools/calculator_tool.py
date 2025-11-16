"""
Calculator Tool - Evaluates mathematical expressions
"""

import math
import re
from typing import Dict, Any
from .base_tool import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """Tool for evaluating mathematical expressions safely."""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Evaluates mathematical expressions. Supports basic arithmetic, trigonometry, and common math functions."
        )
        # Allowed functions and constants
        self.allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")
        }
        self.allowed_names.update({
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
        })
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')"
                }
            },
            "required": ["expression"]
        }
    
    def validate_args(self, **kwargs) -> bool:
        """Validate that expression is provided."""
        return "expression" in kwargs and isinstance(kwargs["expression"], str)
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute calculator tool."""
        expression = kwargs.get("expression", "").strip()
        
        if not expression:
            return ToolResult(
                success=False,
                output=None,
                error="Expression is required"
            )
        
        try:
            # Sanitize expression - only allow safe characters
            if not re.match(r'^[0-9+\-*/().\s,abcdefghijklmnopqrstuvwxyz_]+$', expression.lower()):
                return ToolResult(
                    success=False,
                    output=None,
                    error="Expression contains invalid characters"
                )
            
            # Evaluate expression safely
            result = eval(expression, {"__builtins__": {}}, self.allowed_names)
            
            return ToolResult(
                success=True,
                output={
                    "expression": expression,
                    "result": result,
                    "result_type": type(result).__name__
                },
                metadata={"tool": "calculator"}
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Calculation error: {str(e)}",
                metadata={"tool": "calculator", "error_type": type(e).__name__}
            )

