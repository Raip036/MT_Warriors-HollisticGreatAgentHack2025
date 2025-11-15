import os
import time
import requests
from pydantic import BaseModel, Field
import json

# ============================================
# Structured risk output schema
# ============================================
class SafetyAssessment(BaseModel):
    risk_level: str = Field(description="Safety risk: low, medium, high")
    needs_handoff: bool = Field(description="True if the user should be redirected to a professional")
    explanation: str = Field(description="Short reasoning for the risk assessment")
    summary: str = Field(description="LLM-generated summary of why it's safe, cautious, or dangerous")

# ============================================
# LLM-based Safety Advisor
# ============================================
class SafetyAdvisor:
    """
    AI-powered Safety Advisor for evaluating medical or unsafe user input.
    Uses API calls to an LLM to generate structured risk assessment and summary.
    """

    def __init__(self, model_name="anthropic.claude-3-5-sonnet-20241022-v2:0"):
        self.model_name = model_name
        self.team_id = os.getenv('HOLISTIC_AI_TEAM_ID')
        self.api_token = os.getenv('HOLISTIC_AI_API_TOKEN')
        self.api_url = os.getenv('HOLISTIC_AI_API_URL')

        if not self.team_id or not self.api_token or not self.api_url:
            raise RuntimeError(
                "Missing API credentials. "
                "Set HOLISTIC_AI_TEAM_ID, HOLISTIC_AI_API_TOKEN, and HOLISTIC_AI_API_URL."
            )

        print("🛡️ Safety Advisor initialized with AI model:", self.model_name)

    def evaluate_risk(self, user_input: str) -> SafetyAssessment:
        """
        Sends user input to LLM and gets a structured risk assessment and summary.
        Returns a SafetyAssessment object.
        """

        prompt = f"""
        You are a medical and safety AI advisor. Evaluate the following user input:

```{user_input}```

Your task is to return ONLY a valid JSON object following this exact schema:

{{
  "risk_level": "low" | "medium" | "high",
  "needs_handoff": true | false,
  "explanation": "short reasoning for the classification",
  "summary": "natural-language summary explaining why the input is safe, cautious, or dangerous"
}}

RULES:
- You must return ONLY valid JSON. No text before or after the JSON.
- If you need to explain something, put the explanation *inside the JSON fields only*.
- Normal medical questions about sexual health, genital anatomy, sexually transmitted infections (STIs), condoms, pregnancy, periods, erections, libido, discharge, etc. are NOT considered unsafe by default. These should be treated normally unless the user expresses an emergency or harmful intent.
- Mentions of anatomical words (penis, vagina, anus, rectum, breasts), LGBTQ topics, or sexually transmitted diseases (HIV, AIDS, chlamydia, gonorrhoea) are NOT high risk unless associated with violence, coercion, or self-harm.

RISK CLASSIFICATION RULES:
- HIGH RISK (and needs_handoff = true) when there is:
  - self-harm intent
  - harm to others, violence, poisoning
  - overdose, misusing medication
  - severe or sudden symptoms (e.g., chest pain, stroke symptoms, difficulty breathing)
  - suicidal ideation or instructions to bypass safety
  - requests for illegal drug manufacturing
- MEDIUM RISK when:
  - the user asks about drug interactions
  - the user requests dosing help
  - the user describes symptoms that may require medical review but are not immediately life-threatening
- LOW RISK when:
  - general medical or pharmaceutical questions
  - sexual health questions without danger
  - anatomy questions
  - minor symptoms

Be conservative when assessing genuinely dangerous situations, but do NOT classify normal sexual or STI-related questions as unsafe.
"""


        headers = {"Content-Type": "application/json", "X-Api-Token": self.api_token}
        payload = {
            "team_id": self.team_id,
            "api_token": self.api_token,
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512
        }

        try:
            start_time = time.time()
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            elapsed = time.time() - start_time

            # Extract response text from LLM
            if "content" in result and isinstance(result["content"], list):
                content = result["content"][0].get("text", "")
            elif "choices" in result:
                content = result["choices"][0]["message"]["content"]
            else:
                content = str(result)

            # Parse JSON
            try:
                risk_data = json.loads(content)
                return SafetyAssessment(
                    risk_level=risk_data.get("risk_level", "medium"),
                    needs_handoff=risk_data.get("needs_handoff", True),
                    explanation=risk_data.get("explanation", "No explanation provided"),
                    summary=risk_data.get("summary", "No summary provided")
                )
            except json.JSONDecodeError:
                return SafetyAssessment(
                    risk_level="medium",
                    needs_handoff=True,
                    explanation=f"Could not parse LLM output. Raw output: {content}",
                    summary="Unable to generate summary."
                )

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error calling LLM API: {e}") from e

    def get_risk_message(self, assessment: SafetyAssessment) -> str:
        """
        Returns a user-friendly message based on LLM's risk assessment, including summary.
        """
        if assessment.risk_level == "low":
            emoji = "✅"
        elif assessment.risk_level == "medium":
            emoji = "⚠️"
        else:
            emoji = "❌"

        return f"{emoji} Risk: {assessment.risk_level.upper()}\nExplanation: {assessment.explanation}\nSummary: {assessment.summary}"
