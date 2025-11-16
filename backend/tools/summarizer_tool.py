"""
Summarizer Tool - Summarizes long texts using LLM
"""

import asyncio
from typing import Dict, Any
from .base_tool import BaseTool, ToolResult


class SummarizerTool(BaseTool):
    """Tool for summarizing long texts using the LLM."""
    
    def __init__(self):
        super().__init__(
            name="summarizer",
            description="Summarizes long texts, documents, or instructions into concise summaries. Useful for condensing medication instructions or lengthy documents."
        )
        # Import LLM here to avoid circular imports
        self.llm = None
    
    def _get_llm(self):
        """Lazy load LLM to avoid circular imports."""
        if self.llm is None:
            from agents.agent import get_chat_model
            self.llm = get_chat_model()
        return self.llm
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to summarize"
                },
                "max_length": {
                    "type": "integer",
                    "description": "Maximum length of summary in words (default: 100)",
                    "default": 100
                },
                "focus": {
                    "type": "string",
                    "description": "What to focus on in the summary (e.g., 'key points', 'instructions', 'side effects')",
                    "default": "key points"
                }
            },
            "required": ["text"]
        }
    
    def validate_args(self, **kwargs) -> bool:
        """Validate text is provided."""
        return "text" in kwargs and isinstance(kwargs["text"], str) and len(kwargs["text"].strip()) > 0
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute text summarization."""
        text = kwargs.get("text", "").strip()
        max_length = kwargs.get("max_length", 100)
        focus = kwargs.get("focus", "key points")
        
        if not text:
            return ToolResult(
                success=False,
                output=None,
                error="Text to summarize is required"
            )
        
        if len(text) < 50:
            # Text is already short, return as-is
            return ToolResult(
                success=True,
                output={
                    "original_length": len(text),
                    "summary": text,
                    "summary_length": len(text),
                    "compression_ratio": 1.0
                },
                metadata={"tool": "summarizer", "note": "Text already short"}
            )
        
        # Create summarization prompt
        prompt = f"""Please provide a concise summary of the following text, focusing on {focus}.

Maximum length: {max_length} words.

Text to summarize:
{text}

Summary:"""
        
        try:
            # Get LLM
            llm = self._get_llm()
            
            # Call LLM (this is synchronous, but we're in async context)
            # In a real async implementation, you'd use async LLM calls
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None,
                lambda: llm.invoke([{"role": "user", "content": prompt}])
            )
            
            # Clean up summary
            summary = summary.strip()
            
            return ToolResult(
                success=True,
                output={
                    "original_length": len(text),
                    "summary": summary,
                    "summary_length": len(summary.split()),
                    "compression_ratio": len(text) / max(len(summary), 1),
                    "focus": focus
                },
                metadata={
                    "tool": "summarizer",
                    "max_length_requested": max_length,
                    "focus": focus
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Summarization failed: {str(e)}",
                metadata={"tool": "summarizer", "error_type": type(e).__name__}
            )

