# backend/agents/judge.py

import os
import json
import requests
from typing import Literal
from pydantic import BaseModel, Field

from agents.agent import get_chat_model
from agents.pharma_miku_agent import UserFacingAnswer
from agents.medical_reasoning_agent import MedicalAnswer
from agents.safety_advisor import SafetyAssessment


# ============================================
# Judge Verdict Model
# ============================================
class JudgeVerdict(BaseModel):
    verdict: Literal["SAFE", "BORDERLINE", "UNSAFE"] = Field(
        description="Final safety verdict"
    )
    notes: str = Field(description="What the judge changed or is concerned about")
    adjusted_answer: str = Field(
        default="", description="Safer version if verdict is BORDERLINE or UNSAFE"
    )


# ============================================
# Judge Agent (Agent 5)
# ============================================
class JudgeAgent:
    """
    Agent 5 – Final Safety & Quality Check
    Acts as the final filter before anything is shown to the user.
    Checks safety, factuality, and clarity of the user_facing_answer.
    """

    def __init__(self):
        self.llm = get_chat_model()
        print("⚖️ Judge Agent initialised.")

    def evaluate(
        self,
        user_message: str,
        user_facing_answer: UserFacingAnswer,
        canonical_medical_answer: MedicalAnswer,
        risk_level: str,
        safety_decision: str,
        needs_handoff: bool,
    ) -> JudgeVerdict:
        """
        Evaluates the final answer for safety and quality.
        Returns a verdict and potentially an adjusted answer.
        """

        # Build evaluation prompt
        prompt = f"""
You are a final safety judge for a pharmacy assistant system.

ORIGINAL USER QUESTION:
"{user_message}"

RISK CONTEXT:
- Risk Level: {risk_level}
- Safety Decision: {safety_decision}
- Needs Handoff: {needs_handoff}

CANONICAL MEDICAL ANSWER (internal, professional-level):
{canonical_medical_answer.canonical_answer}

USER-FACING ANSWER (what will be shown to the user):
{user_facing_answer.text}

YOUR TASK:
Evaluate the user-facing answer for:
1. Safety: Does it contain any explicit dosing instructions that are too specific?
2. Completeness: Are important warnings from the canonical answer preserved?
3. Consistency: Does it contradict the canonical medical answer?
4. Clarity: Are safety disclaimers present and clear?

CHECKLIST:
- ❌ UNSAFE if: Contains specific dosing like "take 3 tablets now" or "give 5mg to your 8-year-old"
- ⚠️ BORDERLINE if: Missing important warnings, weak disclaimers, or minor contradictions
- ✅ SAFE if: All warnings preserved, no specific dosing, consistent with canonical answer

RETURN STRICT JSON:
{{
  "verdict": "SAFE" | "BORDERLINE" | "UNSAFE",
  "notes": "What you found or changed",
  "adjusted_answer": "" (only fill if verdict is BORDERLINE or UNSAFE, otherwise empty string)
}}

If verdict is BORDERLINE: Provide an adjusted_answer that adds missing disclaimers or removes overly specific instructions.
If verdict is UNSAFE: Provide a generic safe response that refuses dangerous details and promotes speaking to a doctor.
If verdict is SAFE: Leave adjusted_answer as empty string.
"""

        # Check if LLM is in mock mode
        if hasattr(self.llm, "mock_mode") and self.llm.mock_mode:
            # Mock mode: simple heuristic check
            return self._heuristic_check(
                user_facing_answer, canonical_medical_answer, risk_level, needs_handoff
            )

        # Call LLM for evaluation
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.llm.invoke(messages)

            # Extract text from response
            if isinstance(response, dict):
                if "content" in response and isinstance(response["content"], list):
                    text = response["content"][0].get("text", "")
                elif "completion" in response:
                    text = response["completion"]
                else:
                    text = str(response)
            else:
                text = str(response)

            # Parse JSON response
            try:
                parsed = json.loads(text)
                return JudgeVerdict(
                    verdict=parsed.get("verdict", "BORDERLINE"),
                    notes=parsed.get("notes", "No notes provided"),
                    adjusted_answer=parsed.get("adjusted_answer", ""),
                )
            except json.JSONDecodeError:
                # Fallback to heuristic if JSON parsing fails
                return self._heuristic_check(
                    user_facing_answer,
                    canonical_medical_answer,
                    risk_level,
                    needs_handoff,
                )

        except Exception as e:
            print(f"❗ Judge Agent error: {e}")
            # Fallback to heuristic
            return self._heuristic_check(
                user_facing_answer, canonical_medical_answer, risk_level, needs_handoff
            )

    def _heuristic_check(
        self,
        user_facing_answer: UserFacingAnswer,
        canonical_medical_answer: MedicalAnswer,
        risk_level: str,
        needs_handoff: bool,
    ) -> JudgeVerdict:
        """
        Heuristic fallback when LLM is unavailable.
        Checks for obvious safety issues.
        """
        answer_text = user_facing_answer.text.lower()

        # Check for specific dosing instructions (unsafe patterns)
        unsafe_patterns = [
            "take 3",
            "take 4",
            "take 5",
            "give 5mg",
            "give 10mg",
            "take now",
            "take immediately",
            "you should take",
        ]

        if any(pattern in answer_text for pattern in unsafe_patterns):
            return JudgeVerdict(
                verdict="UNSAFE",
                notes="Contains specific dosing instructions that should not be given to users.",
                adjusted_answer=(
                    "I cannot provide specific dosing instructions. "
                    "Please consult with a doctor or pharmacist who can determine the right dose "
                    "based on your specific situation, age, weight, and medical history."
                ),
            )

        # Check if high risk but missing strong warnings
        if (risk_level == "high" or needs_handoff) and not any(
            word in answer_text
            for word in ["urgent", "emergency", "immediately", "doctor", "pharmacist"]
        ):
            return JudgeVerdict(
                verdict="BORDERLINE",
                notes="High risk situation but missing strong safety warnings.",
                adjusted_answer=(
                    user_facing_answer.text
                    + "\n\n💊 Hey! I want to make sure you're safe - this sounds really important. "
                    "Please talk to a doctor, pharmacist, or call emergency services right away if you need immediate help. "
                    "They're the experts who can give you the best care! ✨"
                ),
            )

        # Default: safe
        return JudgeVerdict(
            verdict="SAFE",
            notes="No obvious safety issues detected.",
            adjusted_answer="",
        )

    def apply_verdict(
        self, verdict: JudgeVerdict, original_answer: UserFacingAnswer
    ) -> UserFacingAnswer:
        """
        Applies the judge's verdict to the answer.
        Returns the original answer if SAFE, or the adjusted answer if BORDERLINE/UNSAFE.
        """
        if verdict.verdict == "SAFE":
            return original_answer

        # Use adjusted answer if provided
        if verdict.adjusted_answer:
            return UserFacingAnswer(
                text=verdict.adjusted_answer,
                age_group=original_answer.age_group,
                tone=original_answer.tone,
                safety_level=original_answer.safety_level,
                needs_handoff=original_answer.needs_handoff,
                safety_message=original_answer.safety_message,
                citations=original_answer.citations,  # Preserve citations
            )

        # Fallback: return original with added warning
        return original_answer

