# backend/agents/input_classifier.py

from typing import Literal
from pydantic import BaseModel, Field


# ============================================
# Structured classification schema
# ============================================
class InputClassification(BaseModel):
    intent: str = Field(description="Detected intent of the user message")
    query_type: Literal["drug_info", "drug_interaction", "general_question"] = \
        Field(description="High-level question type")
    risk_level: Literal["low", "medium", "high"] = \
        Field(description="Safety risk assessment")
    needs_handoff: bool = Field(description="Whether message should be escalated")
    explanation: str = Field(description="Brief classifier explanation")
    age_group: Literal["child", "teen", "adult", "elderly", "unknown"] = \
        Field(default="unknown", description="Detected age group of the user")


# ============================================
# Input Classifier Agent
# ============================================
class InputClassifier:
    """
    Classifies user input for intent, urgency, and potential safety issues.
    """

    EMERGENCY_KEYWORDS = [
        "chest pain", "difficulty breathing", "can't breathe",
        "severe pain", "passing out", "unconscious",
        "internal bleeding", "cannot stop bleeding", "stroke"
    ]

    INJECTION_KEYWORDS = [
        "ignore instructions", "bypass safety", "jailbreak",
        "pretend to", "act as", "malicious"
    ]

    def __init__(self):
        print("🧠 Input Classifier initialised")

    # ------------------------------------------------
    # Basic safety check (prompt injection / empty)
    # ------------------------------------------------
    def is_valid(self, user_input: str) -> bool:
        text = user_input.lower()

        if not user_input.strip():
            return False

        if any(k in text for k in self.INJECTION_KEYWORDS):
            return False

        return True

    def is_safe(self, user_input: str) -> bool:
        return self.is_valid(user_input)

    # ------------------------------------------------
    # Intent + query type detection
    # ------------------------------------------------
    def detect_intent(self, user_input: str) -> str:
        text = user_input.lower()

        # Check for interaction questions FIRST (before "take" matches)
        # Look for patterns like "take X and Y", "X with Y", "mix X and Y"
        interaction_patterns = [
            "interaction", "mix", "combine", "together", 
            "and", "with"  # "take X and Y" or "X with Y"
        ]
        
        # If it mentions combining/using multiple things, check if drugs are mentioned
        if any(pattern in text for pattern in interaction_patterns):
            drug_indicators = [
                "medicine", "medication", "drug", "pill", "tablet", "capsule",
                "ibuprofen", "paracetamol", "aspirin", "tylenol", "advil",
                "acetaminophen", "naproxen", "motrin"
            ]
            # Count how many drug names or indicators appear
            drug_count = sum(1 for drug in drug_indicators if drug in text)
            # If multiple drugs mentioned OR explicit interaction keywords, it's an interaction question
            if drug_count >= 2 or any(kw in text for kw in ["interaction", "mix", "combine"]):
                return "interaction"

        if any(w in text for w in ["side effect", "dosage", "use", "take"]):
            return "informational"

        return "other"

    def classify_query_type(
        self, user_input: str
    ) -> Literal["drug_info", "drug_interaction", "general_question"]:

        intent = self.detect_intent(user_input)

        if intent == "informational":
            return "drug_info"
        if intent == "interaction":
            return "drug_interaction"
        return "general_question"

    # ------------------------------------------------
    # Age group detection
    # ------------------------------------------------
    def detect_age_group(
        self, user_input: str
    ) -> Literal["child", "teen", "adult", "elderly", "unknown"]:
        """
        Detects age group from user input based on language patterns,
        explicit mentions, and context clues.
        """
        text = user_input.lower()

        # Explicit age mentions
        if any(word in text for word in ["i'm 8", "i'm 9", "i'm 10", "i'm 11", "i'm 12", 
                                         "i am 8", "i am 9", "i am 10", "i am 11", "i am 12",
                                         "8 years old", "9 years old", "10 years old", 
                                         "11 years old", "12 years old", "my child", "my kid"]):
            return "child"
        
        if any(word in text for word in ["i'm 13", "i'm 14", "i'm 15", "i'm 16", "i'm 17",
                                         "i am 13", "i am 14", "i am 15", "i am 16", "i am 17",
                                         "13 years old", "14 years old", "15 years old",
                                         "16 years old", "17 years old", "teenager", "teen"]):
            return "teen"
        
        if any(word in text for word in ["i'm 65", "i'm 70", "i'm 75", "i'm 80",
                                         "i am 65", "i am 70", "i am 75", "i am 80",
                                         "65 years old", "70 years old", "75 years old",
                                         "elderly", "senior", "retired", "grandmother", "grandfather"]):
            return "elderly"

        # Language pattern clues
        # Child-like patterns: simple questions, "mom", "dad", "teacher"
        if any(word in text for word in ["mom", "dad", "mommy", "daddy", "teacher", 
                                         "school", "homework", "playground"]):
            return "child"
        
        # Teen patterns: casual language, "like", "omg", slang
        if any(word in text for word in ["like", "omg", "lol", "tbh", "fr", "ngl"]):
            return "teen"
        
        # Elderly patterns: formal language, "doctor", "pharmacist", medical terminology
        if any(word in text for word in ["prescription", "medication", "pharmacist", 
                                         "physician", "appointment"]):
            # Could be adult or elderly, but more likely elderly if using formal terms
            # Default to adult unless other signals
            pass

        # Default to unknown if no clear signals
        return "unknown"

    # ------------------------------------------------
    # Full structured classification
    # ------------------------------------------------
    def classify_input(self, user_input: str) -> InputClassification:
        intent_label = self.detect_intent(user_input)
        query_type = self.classify_query_type(user_input)
        age_group = self.detect_age_group(user_input)
        text = user_input.lower()

        # 🚨 Critical emergencies → must escalate
        if any(word in text for word in self.EMERGENCY_KEYWORDS):
            return InputClassification(
                intent=intent_label,
                query_type=query_type,
                risk_level="high",
                needs_handoff=True,
                explanation="Potential medical emergency detected.",
                age_group=age_group
            )

        # ❌ Unsafe / invalid / prompt-injection attempt
        if not self.is_safe(user_input):
            return InputClassification(
                intent=intent_label,
                query_type=query_type,
                risk_level="high",
                needs_handoff=True,
                explanation="Invalid or unsafe input detected.",
                age_group=age_group
            )

        # ⚠️ Drug interaction → medium risk
        if query_type == "drug_interaction":
            return InputClassification(
                intent=intent_label,
                query_type=query_type,
                risk_level="medium",
                needs_handoff=False,
                explanation="Interaction-related questions require extra caution.",
                age_group=age_group
            )

        # ✅ Safe general question
        return InputClassification(
            intent=intent_label,
            query_type=query_type,
            risk_level="low",
            needs_handoff=False,
            explanation="Safe general health or medication question.",
            age_group=age_group
        )
