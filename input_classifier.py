"""
Input Classifier Agent
- Detects intent
- Classifies query type
- Flags unsafe or suspicious input
"""

from typing import Literal

class InputClassifier:
    """
    Classifies user input for intent, query type, and potential misuse.
    """

    # Define safe query types
    QUERY_TYPES = ["drug_info", "drug_interaction", "general_question"]

    def __init__(self):
        print("🧠 Input Classifier initialized")

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
        Returns a simple label: 'informational', 'interaction', 'other'
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
        # Add more safety checks if needed (regex, AI classifier, etc.)
        return True
