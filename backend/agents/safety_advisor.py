# backend/agents/safety_advisor.py

import os
import time
import json
import requests
from pydantic import BaseModel, Field

from agents.input_classifier import InputClassification


# ============================================
# Structured Safety Output
# ============================================
class SafetyAssessment(BaseModel):
    risk_level: str = Field(description="low | medium | high")
    needs_handoff: bool = Field(description="If the user should be referred to a clinician")
    explanation: str = Field(description="LLM explanation for risk classification")
    summary: str = Field(description="Plain-language user-facing summary")


# ============================================
# SAFETY ADVISOR — Bedrock-Compatible
# ============================================
class SafetyAdvisor:
    """
    Evaluates user input for medical risk.
    Uses Bedrock Claude 3.5 Sonnet format.
    """

    def __init__(self, model_name="anthropic.claude-3-5-sonnet-20241022-v2:0"):
        self.model_name = model_name
        self.api_url = os.getenv("HOLISTIC_AI_API_URL")
        self.api_token = os.getenv("HOLISTIC_AI_API_TOKEN")
        self.team_id = os.getenv("HOLISTIC_AI_TEAM_ID")

        # Check credentials
        if not self.api_url or not self.api_token or not self.team_id:
            print("⚠️ SafetyAdvisor: MOCK MODE — missing API credentials.")
            self.mock_mode = True
        else:
            self.mock_mode = False
            print("🛡️ Safety Advisor initialised with model:", self.model_name)

    # ============================================
    # Main Safety Scoring Function
    # ============================================
    def evaluate_risk(self, user_input: str, classification: InputClassification) -> SafetyAssessment:

        # -----------------------------------------------
        # MOCK MODE
        # -----------------------------------------------
        if self.mock_mode:
            return SafetyAssessment(
                risk_level=classification.risk_level,
                needs_handoff=classification.needs_handoff,
                explanation="Mock mode: returning classifier result only.",
                summary="(Mock mode) No real safety evaluation performed."
            )

        # -----------------------------------------------
        # Build prompt
        # -----------------------------------------------
        prompt = f"""
You are a medical safety evaluation model.

Evaluate the following user message:

USER MESSAGE:
\"\"\"{user_input}\"\"\"

INITIAL CLASSIFICATION:
- intent: {classification.intent}
- heuristic risk: {classification.risk_level}
- classifier explanation: {classification.explanation}
- needs_handoff (initial): {classification.needs_handoff}

POLICY:
- Escalate HIGH risk symptoms (chest pain, overdose, severe pain, difficulty breathing) → needs_handoff: true
- MEDIUM risk for drug interaction or dosing questions → needs_handoff: false (allow through with warnings)
- LOW risk for safe informational requests (e.g., "what is X?", "how does Y work?") → needs_handoff: false (ALWAYS allow through)
- Drug interaction questions (e.g., "can I take X with Y?") should be ALLOWED to proceed so the system can look up evidence. Set risk_level: "medium" and needs_handoff: false.
- General drug information questions should be LOW risk and needs_handoff: false - these are safe to answer with evidence.
- Only set needs_handoff: true for true emergencies, self-harm situations, or when user is asking for specific dosing for a specific person.
- Be permissive: When in doubt, allow the question through (needs_handoff: false) so the system can provide evidence-based answers.
- Override classifier if incorrect, but explain why.

RETURN STRICT JSON:
{{
  "risk_level": "low" | "medium" | "high",
  "needs_handoff": true | false,
  "explanation": "Reason for classification",
  "summary": "User-facing explanation"
}}
"""

        # -----------------------------------------------
        # Bedrock Claude 3.5 Payload (Fixed Schema)
        # -----------------------------------------------
        payload = {
            "team_id": self.team_id,
            "api_token": self.api_token,
            "model": self.model_name,
            "max_tokens": 512,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json",
            "X-Api-Token": self.api_token
        }

        # -----------------------------------------------
        # API CALL
        # -----------------------------------------------
        try:
            start = time.time()
            response = requests.post(self.api_url, headers=headers, data=json.dumps(payload), timeout=60)
            print("🔍 SafetyAdvisor Status:", response.status_code)
            print("🔍 SafetyAdvisor Raw:", response.text)

            response.raise_for_status()
            result = response.json()
            latency = time.time() - start

            # Extract Claude Output
            if "content" in result and isinstance(result["content"], list):
                model_text = result["content"][0].get("text", "")
            elif "completion" in result:
                model_text = result["completion"]
            else:
                model_text = str(result)

            # Attempt JSON parsing
            try:
                parsed = json.loads(model_text)

                return SafetyAssessment(
                    risk_level=parsed.get("risk_level", "medium"),
                    needs_handoff=parsed.get("needs_handoff", True),
                    explanation=parsed.get("explanation", "No explanation provided"),
                    summary=parsed.get("summary", "No summary provided")
                )

            except json.JSONDecodeError:
                # Safety fallback
                return SafetyAssessment(
                    risk_level="medium",
                    needs_handoff=True,
                    explanation=f"LLM returned invalid JSON. Raw: {model_text}",
                    summary="Unable to parse safety evaluation."
                )

        except Exception as e:
            # Hard failure fallback
            return SafetyAssessment(
                risk_level="medium",
                needs_handoff=True,
                explanation=f"Safety Advisor API error: {e}",
                summary="A system error occurred evaluating safety."
            )

    # ============================================
    # Pretty User-Friendly Formatting
    # ============================================
    def get_risk_message(self, assessment: SafetyAssessment) -> str:
        emoji = {"low": "✅", "medium": "⚠️", "high": "❌"}.get(assessment.risk_level, "⚠️")
        return f"{emoji} Risk: {assessment.risk_level.upper()}\nExplanation: {assessment.explanation}\nSummary: {assessment.summary}"


