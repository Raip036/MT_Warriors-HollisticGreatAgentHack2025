# backend/agents/trace_explainer.py

from typing import Dict, Any
from pydantic import BaseModel, Field

from agents.agent import get_chat_model


# ============================================
# Trace Explanation Model
# ============================================
class TraceExplanation(BaseModel):
    trace_explanation_technical: str = Field(
        description="Explanation for developers / auditors"
    )
    trace_explanation_user_friendly: str = Field(
        description="Simple explanation for users"
    )
    trace_summary: Dict[str, Any] = Field(
        default_factory=dict, description="Structured summary of key steps"
    )


# ============================================
# Trace Explainer Agent (Agent 6)
# ============================================
class TraceExplainerAgent:
    """
    Agent 6 – Glass Box Reasoning / Trace Explainer
    Turns the internal trace into human-readable explanations.
    Supports debugging, observability, and hackathon evaluation.
    """

    def __init__(self):
        self.llm = get_chat_model()
        print("🔍 Trace Explainer Agent initialised.")

    def explain(
        self,
        trace: Dict[str, Any],
        user_message: str,
        final_answer: str,
    ) -> TraceExplanation:
        """
        Generates both technical and user-friendly explanations from the trace.
        """

        # Build technical explanation prompt
        technical_prompt = f"""
You are generating a technical explanation of a multi-agent pharmacy assistant pipeline.

USER QUESTION:
"{user_message}"

FINAL ANSWER:
"{final_answer}"

TRACE DATA (JSON):
{self._format_trace_for_llm(trace)}

Generate a technical explanation that describes:
1. How the input was classified (intent, risk level, age group)
2. How the safety decision was made
3. Which tools were called (Valyu, LLM) and why
4. How the canonical medical answer was built
5. How PharmaMiku rephrased it
6. What the Judge Agent checked

Write in clear, structured format suitable for developers and auditors.
Do NOT reveal API keys, exact prompts, or internal implementation details.
Focus on the reasoning flow and decision points.
"""

        # Build user-friendly explanation prompt
        user_friendly_prompt = f"""
You are explaining how a pharmacy assistant answered a question, in simple language.

USER QUESTION:
"{user_message}"

FINAL ANSWER:
"{final_answer}"

TRACE SUMMARY:
{self._format_trace_summary(trace)}

Generate a simple, friendly explanation that describes:
- What the assistant did step-by-step
- Why certain safety checks were made
- How trusted sources were used
- What the final answer is based on

Write as if explaining to a curious user (could be a child, teen, or adult).
Use simple language. Avoid technical jargon.
Do NOT mention "agents", "LLM", "API calls", or technical implementation details.
Instead, say things like "I checked if your question was safe", "I looked up trusted medicine sources", etc.
"""

        # Generate explanations
        technical_explanation = self._generate_explanation(technical_prompt)
        user_friendly_explanation = self._generate_explanation(user_friendly_prompt)

        # Build structured summary
        trace_summary = self._build_trace_summary(trace)

        return TraceExplanation(
            trace_explanation_technical=technical_explanation,
            trace_explanation_user_friendly=user_friendly_explanation,
            trace_summary=trace_summary,
        )

    def _generate_explanation(self, prompt: str) -> str:
        """Generates an explanation using the LLM or returns a fallback."""
        if hasattr(self.llm, "mock_mode") and self.llm.mock_mode:
            return self._mock_explanation(prompt)

        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm.invoke(messages)

            # Extract text
            if isinstance(response, dict):
                if "content" in response and isinstance(response["content"], list):
                    return response["content"][0].get("text", "")
                elif "completion" in response:
                    return response["completion"]
                else:
                    return str(response)
            else:
                return str(response)

        except Exception as e:
            print(f"❗ Trace Explainer error: {e}")
            return self._mock_explanation(prompt)

    def _mock_explanation(self, prompt: str) -> str:
        """Fallback explanation when LLM is unavailable."""
        if "technical" in prompt.lower():
            return (
                "Technical explanation: The system processed the question through "
                "multiple safety and reasoning stages, consulted trusted medical sources, "
                "and generated a safe, user-friendly response."
            )
        else:
            return (
                "I checked if your question was safe to answer, looked up information "
                "from trusted medicine sources, and then explained it in a way that's "
                "easy to understand. I also made sure to include important safety reminders."
            )

    def _format_trace_for_llm(self, trace: Dict[str, Any]) -> str:
        """Formats trace data for LLM consumption, removing sensitive info."""
        import json

        # Create a sanitized copy
        sanitized = {}
        for key, value in trace.items():
            if isinstance(value, dict):
                # Remove any sensitive fields
                sanitized_value = {
                    k: v
                    for k, v in value.items()
                    if k not in ["api_key", "token", "secret", "password"]
                }
                sanitized[key] = sanitized_value
            else:
                sanitized[key] = value

        try:
            return json.dumps(sanitized, indent=2)
        except:
            return str(sanitized)

    def _format_trace_summary(self, trace: Dict[str, Any]) -> str:
        """Creates a simple summary of the trace for user-friendly explanation."""
        summary_parts = []

        if "input_classifier" in trace:
            cls = trace["input_classifier"]
            summary_parts.append(
                f"Intent: {cls.get('intent', 'unknown')}, "
                f"Risk: {cls.get('risk_level', 'unknown')}"
            )

        if "safety_advisor" in trace:
            safety = trace["safety_advisor"]
            summary_parts.append(
                f"Safety check: {safety.get('risk_level', 'unknown')} risk"
            )

        if "medical_reasoning" in trace:
            summary_parts.append("Consulted trusted medical sources")

        if "pharma_miku" in trace:
            summary_parts.append("Adapted answer for user")

        if "judge" in trace:
            summary_parts.append("Final safety check completed")

        return " | ".join(summary_parts) if summary_parts else "Processed through safety and reasoning pipeline"

    def _build_trace_summary(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """Builds a structured summary of key steps."""
        summary = {
            "steps": [],
            "risk_level": "unknown",
            "safety_decision": "unknown",
            "sources_used": False,
        }

        # Extract key information
        if "input_classifier" in trace:
            cls = trace["input_classifier"]
            summary["steps"].append("Input Classification")
            summary["risk_level"] = cls.get("risk_level", "unknown")
            summary["age_group"] = cls.get("age_group", "unknown")

        if "safety_advisor" in trace:
            safety = trace["safety_advisor"]
            summary["steps"].append("Safety Evaluation")
            summary["safety_decision"] = safety.get("risk_level", "unknown")
            summary["needs_handoff"] = safety.get("needs_handoff", False)

        if "medical_reasoning" in trace:
            summary["steps"].append("Medical Reasoning")
            med = trace["medical_reasoning"]
            summary["sources_used"] = len(med.get("citations", [])) > 0
            summary["citation_count"] = len(med.get("citations", []))

        if "pharma_miku" in trace:
            summary["steps"].append("Persona Adaptation")

        if "judge" in trace:
            summary["steps"].append("Final Safety Check")
            judge = trace["judge"]
            summary["judge_verdict"] = judge.get("verdict", "unknown")

        return summary

