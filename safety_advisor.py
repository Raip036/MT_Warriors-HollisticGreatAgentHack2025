"""
Safety Advisor Agent
- Performs risk assessment
- Evaluates medical safety concerns
- Determines risk level
"""

from typing import Literal

class SafetyAdvisor:
    """
    Evaluates user input for medical and prompt safety risks.
    """

    def __init__(self):
        print("🛡️  Safety Advisor initialized")

    def evaluate_risk(self, user_input: str) -> Literal["low", "medium", "high"]:
        """
        Determines the risk level of a query:
        - low: safe, general questions
        - medium: requires caution, sensitive info
        - high: unsafe, potentially harmful or malicious
        """
        user_input_lower = user_input.lower()

        # High-risk indicators
        high_risk_keywords = [
            "self-harm", "suicide", "inject", "illegal", "bypass safety", 
            "ignore instructions", "harmful", "poison", "malicious"
        ]
        for keyword in high_risk_keywords:
            if keyword in user_input_lower:
                return "high"

        # Medium-risk indicators
        medium_risk_keywords = [
            "dosage", "combine drugs", "interaction", "pregnant", "child", "elderly"
        ]
        for keyword in medium_risk_keywords:
            if keyword in user_input_lower:
                return "medium"

        # Otherwise, low risk
        return "low"

    def is_safe(self, user_input: str) -> bool:
        """
        Quick boolean safety check
        """
        risk = self.evaluate_risk(user_input)
        return risk == "low"

    def get_risk_message(self, user_input: str) -> str:
        """
        Returns a message indicating the risk assessment
        """
        risk = self.evaluate_risk(user_input)
        if risk == "low":
            return "✅ Input is low risk and safe to process."
        elif risk == "medium":
            return "⚠️ Input is medium risk. Exercise caution."
        else:
            return "❌ Input is high risk. Cannot process safely."
