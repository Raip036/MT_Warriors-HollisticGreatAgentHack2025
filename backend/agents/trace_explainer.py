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
You are explaining how a pharmacy assistant answered a question, in simple language that anyone can understand.

USER QUESTION:
"{user_message}"

FINAL ANSWER:
"{final_answer}"

TRACE SUMMARY:
{self._format_trace_summary(trace)}

Generate a simple, friendly explanation that describes HOW I found this answer, written for someone who:
- Is not familiar with AI or technology
- Is not a medical professional
- Just wants to understand how I arrived at this information

IMPORTANT GUIDELINES:
1. Use everyday language - like explaining to a friend or family member
2. Use analogies when helpful (e.g., "like checking a library" instead of "searching a database")
3. Explain WHY I did each step, not just WHAT I did
4. Make it feel personal and conversational (use "I" and "you")
5. Keep it brief (2-4 sentences max) but meaningful

FORBIDDEN WORDS/PHRASES (never use these):
- "AI", "artificial intelligence", "machine learning", "LLM", "model"
- "API", "endpoint", "system", "pipeline", "agent", "algorithm"
- "Bedrock", "Claude", "Valyu" (brand names)
- "technical", "computational", "processing"
- "data", "dataset", "database" (use "sources" or "information" instead)

APPROVED LANGUAGE (use these instead):
- "I looked up information" instead of "I queried a database"
- "trusted medical sources" instead of "evidence base"
- "I made sure it was safe" instead of "I performed a safety evaluation"
- "I double-checked" instead of "I ran a validation check"
- "I explained it simply" instead of "I applied a persona layer"

Write the explanation as if I'm telling the user directly, like:
"I wanted to make sure I gave you the right information, so I first checked if your question was something I could safely answer. Then I looked up what trusted medical sources say about this topic. After finding reliable information, I made sure to explain it in a way that's easy to understand, and I double-checked that everything was safe and accurate before sharing it with you."
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
                "I wanted to make sure I gave you the right information, so I first checked "
                "if your question was something I could safely answer. Then I looked up what "
                "trusted medical sources say about this topic. After finding reliable information, "
                "I made sure to explain it in a way that's easy to understand, and I double-checked "
                "that everything was safe and accurate before sharing it with you."
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
            intent = cls.get('intent', 'unknown')
            risk = cls.get('risk_level', 'unknown')
            # Convert to user-friendly language
            intent_map = {
                'drug_info': 'asking about a medication',
                'drug_interaction': 'asking about mixing medications',
                'dosage': 'asking about how much to take',
                'side_effects': 'asking about side effects',
                'general': 'asking a general question'
            }
            friendly_intent = intent_map.get(intent, intent)
            summary_parts.append(f"Your question was about {friendly_intent}")

        if "safety_advisor" in trace:
            safety = trace["safety_advisor"]
            risk_level = safety.get('risk_level', 'unknown')
            if risk_level == 'low':
                summary_parts.append("I determined this was a safe question to answer")
            elif risk_level == 'medium':
                summary_parts.append("I noted this question needs some caution")
            else:
                summary_parts.append("I checked the safety of answering this")

        if "medical_reasoning" in trace:
            med = trace["medical_reasoning"]
            citation_count = len(med.get("citations", []))
            if citation_count > 0:
                summary_parts.append(f"I found information from {citation_count} trusted medical source(s)")
            else:
                summary_parts.append("I looked up information from trusted medical sources")

        if "pharma_miku" in trace:
            summary_parts.append("I explained it in simple, easy-to-understand language")

        if "judge" in trace:
            judge = trace["judge"]
            verdict = judge.get("verdict", "unknown")
            if verdict == "SAFE":
                summary_parts.append("I double-checked everything to make sure it was safe and accurate")

        return " | ".join(summary_parts) if summary_parts else "I processed your question through safety checks and looked up trusted information"

    def _build_trace_summary(self, trace: Dict[str, Any]) -> Dict[str, Any]:
        """Builds a structured summary of key steps for complete traceability."""
        summary = {
            "steps": [],
            "execution_path": [],
            "risk_level": "unknown",
            "safety_decision": "unknown",
            "sources_used": False,
            "citation_count": 0,
        }

        # Build detailed execution path for traceability
        execution_path = []

        # Step 1: Input Classification
        if "input_classifier" in trace:
            cls = trace["input_classifier"]
            summary["steps"].append("Input Classification")
            summary["risk_level"] = cls.get("risk_level", "unknown")
            summary["age_group"] = cls.get("age_group", "unknown")
            execution_path.append({
                "step": 1,
                "name": "Input Classification",
                "status": "completed",
                "intent": cls.get("intent", "unknown"),
                "risk_level": cls.get("risk_level", "unknown"),
                "explanation": cls.get("explanation", ""),
            })

        # Step 2: Safety Evaluation
        if "safety_advisor" in trace:
            safety = trace["safety_advisor"]
            summary["steps"].append("Safety Evaluation")
            summary["safety_decision"] = safety.get("risk_level", "unknown")
            summary["needs_handoff"] = safety.get("needs_handoff", False)
            execution_path.append({
                "step": 2,
                "name": "Safety Evaluation",
                "status": "completed",
                "risk_level": safety.get("risk_level", "unknown"),
                "needs_handoff": safety.get("needs_handoff", False),
                "explanation": safety.get("explanation", ""),
                "summary": safety.get("summary", ""),
            })

        # Step 3: Medical Reasoning
        if "medical_reasoning" in trace:
            summary["steps"].append("Medical Reasoning")
            med = trace["medical_reasoning"]
            citation_count = len(med.get("citations", []))
            summary["sources_used"] = citation_count > 0
            summary["citation_count"] = citation_count
            execution_path.append({
                "step": 3,
                "name": "Medical Reasoning",
                "status": "completed",
                "citations": med.get("citations", []),
                "citation_count": citation_count,
                "has_evidence": citation_count > 0,
            })

        # Step 4: Persona Adaptation
        if "pharma_miku" in trace:
            summary["steps"].append("Persona Adaptation")
            pharma = trace["pharma_miku"]
            execution_path.append({
                "step": 4,
                "name": "Persona Adaptation",
                "status": "completed",
                "age_group": pharma.get("age_group", "unknown"),
                "tone": pharma.get("tone", ""),
            })

        # Step 5: Final Safety Check (Judge)
        if "judge" in trace:
            summary["steps"].append("Final Safety Check")
            judge = trace["judge"]
            summary["judge_verdict"] = judge.get("verdict", "unknown")
            execution_path.append({
                "step": 5,
                "name": "Final Safety Check",
                "status": "completed",
                "verdict": judge.get("verdict", "unknown"),
                "notes": judge.get("notes", ""),
            })

        summary["execution_path"] = execution_path
        return summary

