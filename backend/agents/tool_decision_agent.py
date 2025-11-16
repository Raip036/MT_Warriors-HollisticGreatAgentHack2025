"""
Tool Decision Agent - Decides which tool to call based on user input
"""

import json
from typing import Dict, List, Optional, Any
from agents.agent import get_chat_model
from tools import get_tool_manager


class ToolDecision:
    """Result of tool decision process."""
    def __init__(self, tool_name: Optional[str] = None, arguments: Optional[Dict] = None, reasoning: str = ""):
        self.tool_name = tool_name
        self.arguments = arguments or {}
        self.reasoning = reasoning
        self.should_use_tool = tool_name is not None


class ToolDecisionAgent:
    """
    Agent that decides which tool to call based on user input.
    Uses LLM to analyze the request and select appropriate tools.
    """
    
    def __init__(self):
        self.llm = get_chat_model()
        self.tool_manager = get_tool_manager()
    
    def decide_tool(self, user_input: str, context: Optional[Dict] = None) -> ToolDecision:
        """
        Decide which tool to call based on user input.
        
        Args:
            user_input: User's input/question
            context: Optional context from previous steps
        
        Returns:
            ToolDecision with tool_name, arguments, and reasoning
        """
        # Get available tools
        available_tools = self.tool_manager.list_tools()
        
        if not available_tools:
            return ToolDecision(
                tool_name=None,
                reasoning="No tools available"
            )
        
        # Build prompt for tool selection
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in available_tools
        ])
        
        prompt = f"""You are a tool selection agent. Analyze the user's request and decide which tool (if any) should be called.

Available tools:
{tools_description}

User request: {user_input}

Context: {json.dumps(context or {}, indent=2)}

Instructions:
1. Determine if any tool is needed to fulfill the user's request
2. If a tool is needed, select the most appropriate one
3. Extract the arguments for the tool from the user's request
4. Provide your reasoning

Respond in JSON format:
{{
    "tool_name": "name_of_tool_or_null",
    "arguments": {{"arg1": "value1", ...}},
    "reasoning": "Why you selected this tool or why no tool is needed"
}}

If no tool is needed, set tool_name to null."""
        
        try:
            # Call LLM
            response = self.llm.invoke([{"role": "user", "content": prompt}])
            
            # Parse response
            response_text = response.strip()
            
            # Try to extract JSON from response
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Try to find JSON object
            if "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                response_text = response_text[json_start:json_end]
            
            decision_data = json.loads(response_text)
            
            tool_name = decision_data.get("tool_name")
            if tool_name == "null" or tool_name is None:
                tool_name = None
            
            return ToolDecision(
                tool_name=tool_name,
                arguments=decision_data.get("arguments", {}),
                reasoning=decision_data.get("reasoning", "No reasoning provided")
            )
            
        except Exception as e:
            # Fallback: simple keyword matching
            return self._fallback_decision(user_input)
    
    def _fallback_decision(self, user_input: str) -> ToolDecision:
        """Fallback decision using keyword matching."""
        user_lower = user_input.lower()
        
        # Calculator
        if any(keyword in user_lower for keyword in ["calculate", "math", "compute", "+", "-", "*", "/", "="]):
            return ToolDecision(
                tool_name="calculator",
                arguments={"expression": user_input},
                reasoning="Detected mathematical expression or calculation request"
            )
        
        # Drug info
        if any(keyword in user_lower for keyword in ["drug", "medication", "medicine", "paracetamol", "ibuprofen", "aspirin", "dosage", "side effect"]):
            # Try to extract drug name
            drug_name = None
            for drug in ["paracetamol", "ibuprofen", "aspirin"]:
                if drug in user_lower:
                    drug_name = drug
                    break
            
            if drug_name:
                return ToolDecision(
                    tool_name="drug_info",
                    arguments={"drug_name": drug_name, "info_type": "all"},
                    reasoning=f"Detected request for information about {drug_name}"
                )
        
        # Summarizer
        if any(keyword in user_lower for keyword in ["summarize", "summary", "brief", "condense", "short version"]):
            return ToolDecision(
                tool_name="summarizer",
                arguments={"text": user_input, "max_length": 100},
                reasoning="Detected summarization request"
            )
        
        # Reminder
        if any(keyword in user_lower for keyword in ["remind", "reminder", "schedule", "alert", "notify"]):
            return ToolDecision(
                tool_name="reminder",
                arguments={
                    "message": user_input,
                    "reminder_time": "in 1 hour",  # Default
                    "reminder_type": "medication"
                },
                reasoning="Detected reminder/scheduling request"
            )
        
        return ToolDecision(
            tool_name=None,
            reasoning="No matching tool found for this request"
        )

