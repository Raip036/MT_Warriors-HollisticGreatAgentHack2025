from typing import Literal
from pydantic import BaseModel, Field

# ============================================
# Structured classification schema
# ============================================
class InputClassification(BaseModel):
    intent: str = Field(description="Detected intent of the user message")
    risk_level: str = Field(description="Safety risk: low, medium, high")
    needs_handoff: bool = Field(description="True if message should be escalated")
    explanation: str = Field(description="Brief explanation of classification")


# ============================================
# Input Classifier Agent
# ============================================
class InputClassifier:
    """
    Classifies user input for intent, query type, and potential misuse.
    """

    QUERY_TYPES = ["drug_info", "drug_interaction", "general_question"]

    def __init__(self):
        print("🧠 Input Classifier initialized")

    # ------------------------------------------------
    # Low-level safety check
    # ------------------------------------------------
    def is_valid(self, user_input: str) -> bool:
        suspicious_keywords = [
            "ignore instructions",
            "bypass safety",
            "do anything",
            "malicious"
        ]
        for keyword in suspicious_keywords:
            if keyword.lower() in user_input.lower():
                return False
        return bool(user_input.strip())

    def is_safe(self, user_input: str) -> bool:
        """High-level safety check wrapper."""
        return self.is_valid(user_input)

    # ------------------------------------------------
    # Intent + query type detection
    # ------------------------------------------------
    def detect_intent(self, user_input: str) -> str:
        user_input_lower = user_input.lower()

        if any(w in user_input_lower for w in ["side effect", "dosage", "use", "take"]):
            return "informational"
        elif any(w in user_input_lower for w in ["interaction", "mix", "combine"]):
            return "interaction"
        else:
            return "other"

    def classify_query_type(self, user_input: str) -> Literal["drug_info", "drug_interaction", "general_question"]:
        intent = self.detect_intent(user_input)
        if intent == "informational":
            return "drug_info"
        elif intent == "interaction":
            return "drug_interaction"
        else:
            return "general_question"

    # ------------------------------------------------
    # Structured classification
    # ------------------------------------------------
    def classify_input(self, user_input: str) -> InputClassification:
        intent_label = self.detect_intent(user_input)

        # Safety categories
        if not self.is_safe(user_input):
            return InputClassification(
                intent=intent_label,
                risk_level="high",
                needs_handoff=True,
                explanation="Unsafe input detected (prompt injection or empty input)."
            )

        elif any(x in user_input.lower() for x in [
            "chest pain", "difficulty breathing", "overdose", "severe pain"
        ]):
            return InputClassification(
                intent=intent_label,
                risk_level="high",
                needs_handoff=True,
                explanation="Potential medical emergency detected."
            )

        elif intent_label == "interaction":
            return InputClassification(
                intent=intent_label,
                risk_level="medium",
                needs_handoff=False,
                explanation="Drug interaction questions require extra caution."
            )

        return InputClassification(
            intent=intent_label,
            risk_level="low",
            needs_handoff=False,
            explanation="General safe informational question."
        )
