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
    Combines simple heuristics with structured output for safety.
    """

    # Define safe query types
    QUERY_TYPES = ["drug_info", "drug_interaction", "general_question"]

    def __init__(self):
        print("🧠 Input Classifier initialized")

    # --------------------------------------------
    # Low-level checks
    # --------------------------------------------
    def is_valid(self, user_input: str) -> bool:
        """
        Quick check for empty input or suspicious prompt injection patterns
        """
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

    def detect_intent(self, user_input: str) -> str:
        """
        Detects the user's intent.
        Returns: 'informational', 'interaction', or 'other'
        """
        user_input_lower = user_input.lower()
        if any(word in user_input_lower for word in ["side effect", "dosage", "use", "take"]):
            return "informational"
        elif any(word in user_input_lower for word in ["interaction", "mix", "combine"]):
            return "interaction"
        else:
            return "other"

    def classify_query_type(self, user_input: str) -> Literal["drug_info", "drug_interaction", "general_question"]:
        """
        Classify input into one of the predefined query types
        """
        intent = self.detect_intent(user_input)
        if intent == "informational":
            return "drug_info"
        elif intent == "interaction":
            return "drug_interaction"
        else:
            return "general_question"

    def is_safe(self, user_input: str) -> bool:
        """
        High-level safety check for prompt misuse / injections
        """
        if not self.is_valid(user_input):
            return False
        # Add more safety checks if needed
        return True

    # --------------------------------------------
    # Structured classification
    # --------------------------------------------
    def classify_input(self, user_input: str) -> InputClassification:
        """
        Returns a structured classification:
        - intent
        - risk_level
        - needs_handoff
        - explanation
        """
        # Detect intent
        intent_label = self.detect_intent(user_input)

        # Determine risk_level
        if not self.is_safe(user_input):
            risk_level = "high"
            needs_handoff = True
            explanation = "Unsafe input detected (suspicious keywords or empty input). Escalate."
        elif any(word in user_input.lower() for word in ["chest pain", "difficulty breathing", "overdose", "severe pain"]):
            risk_level = "high"
            needs_handoff = True
            explanation = "Potential medical emergency. Escalate to professional."
        elif intent_label == "interaction":
            risk_level = "medium"
            needs_handoff = False
            explanation = "Interaction question detected; user should double-check with pharmacist."
        else:
            risk_level = "low"
            needs_handoff = False
            explanation = "Standard informational or general question; safe to answer."

        return InputClassification(
            intent=intent_label,
            risk_level=risk_level,
            needs_handoff=needs_handoff,
            explanation=explanation
        )
