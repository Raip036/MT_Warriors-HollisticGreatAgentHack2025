# backend/agents/medical_reasoning_agent.py

import os
from typing import List

from pydantic import BaseModel, Field

from agents.agent import get_chat_model
from agents.input_classifier import InputClassification
from agents.safety_advisor import SafetyAssessment

# Try to import Valyu, but don't crash if it's not installed
try:
    from valyu import Valyu
    HAS_VALYU = True
except ImportError:
    HAS_VALYU = False


# ============================================
# Data models
# ============================================

class EvidenceItem(BaseModel):
    title: str = Field("", description="Title of the evidence source")
    url: str = Field("", description="Link to the source")
    content: str = Field("", description="Short excerpt or content from the source")


class MedicalAnswer(BaseModel):
    canonical_answer: str
    warnings: str
    citations: List[str] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)


# ============================================
# Medical Reasoning Agent (Agent 3)
# ============================================

class MedicalReasoningAgent:
    """
    Agent 3 – the 'doctor brain':
    - Fetch high-quality evidence using Valyu DeepSearch.
    - Ask Claude 3.5 Sonnet (via Bedrock) to synthesise a clinically safe, correct answer.
    - Return structured result.
    """

    def __init__(self):
        self.llm = get_chat_model()

        # Valyu setup
        self.valyu_api_key = os.getenv("VALYU_API_KEY")
        self.mock_mode = False
        self.valyu_client = None

        if HAS_VALYU and self.valyu_api_key:
            self.valyu_client = Valyu(api_key=self.valyu_api_key)
            print("🩺 MedicalReasoningAgent: Valyu DeepSearch enabled.")
        else:
            self.mock_mode = True
            missing = []
            if not HAS_VALYU:
                missing.append("valyu not installed")
            if not self.valyu_api_key:
                missing.append("VALYU_API_KEY missing")
            print(f"⚠️ MedicalReasoningAgent: MOCK MODE ({' & '.join(missing)})")

    # ----------------------------------------
    # Evidence retrieval
    # ----------------------------------------
    def fetch_evidence(self, query: str, max_results: int = 5) -> List[EvidenceItem]:

        if self.mock_mode or not self.valyu_client:
            return [
                EvidenceItem(
                    title="Mock Evidence Example",
                    url="https://example.com/mock",
                    content=(
                        "Ibuprofen and paracetamol can be combined safely "
                        "if dosed correctly. Always follow NHS or packaging guidelines."
                    ),
                )
            ]

        response = self.valyu_client.search(query)
        items: List[EvidenceItem] = []

        for r in getattr(response, "results", []):
            items.append(
                EvidenceItem(
                    title=getattr(r, "title", "") or "",
                    url=getattr(r, "url", "") or "",
                    content=getattr(r, "content", "") or "",
                )
            )

        if not items:
            items.append(
                EvidenceItem(
                    title="No documents found",
                    url="",
                    content="No specific documents returned; answer will reflect uncertainty.",
                )
            )

        return items

    # ----------------------------------------
    # Main reasoning pipeline
    # ----------------------------------------
    def run(
        self,
        user_input: str,
        classification: InputClassification,
        safety: SafetyAssessment,
    ) -> MedicalAnswer:

        # Prepare Valyu search
        query = f"{user_input} (intent={classification.intent})"
        evidence_items = self.fetch_evidence(query)
        citations = [e.url for e in evidence_items if e.url]

        evidence_text = "\n\n".join(
            f"[{i+1}] {e.title}\nURL: {e.url}\n{e.content}"
            for i, e in enumerate(evidence_items)
        )

        # System instructions merged into user message (Bedrock compatible)
        full_prompt = f"""
SYSTEM INSTRUCTIONS:
You are a clinical pharmacist / medical expert providing evidence-based information.
Your goal is to ANSWER the user's question using the provided evidence.

USER QUESTION:
{user_input}

PREVIOUS AGENT CONTEXT:
- intent: {classification.intent}
- heuristic risk: {classification.risk_level}
- safety risk: {safety.risk_level}
- needs_handoff: {safety.needs_handoff}

EVIDENCE FROM VALYU:
{evidence_text}

TASKS:
1. Provide a clear, informative answer based on the evidence provided.
2. If evidence is available, USE IT to answer the question directly.
3. Include key facts, mechanisms, uses, and safety information from the evidence.
4. State any relevant cautions or warnings from the evidence.
5. If evidence is missing or incomplete, say so, but still provide what you can from the evidence that IS available.
6. Be helpful and informative - the user wants to learn about medications.

IMPORTANT: When evidence is provided, you should give a substantive answer. Don't just defer to doctors - provide the information from the sources, then remind them to consult a professional for personalized advice.
"""

        # Bedrock-safe: ONLY user/assistant roles allowed
        messages = [
            {"role": "user", "content": full_prompt}
        ]

        try:
            llm_response = self.llm.invoke(messages)

            # Some wrappers return a dict with `text`, some return raw text
            if isinstance(llm_response, dict) and "text" in llm_response:
                answer_text = llm_response["text"]
            else:
                answer_text = str(llm_response)

        except Exception as e:
            print("❗ MedicalReasoningAgent LLM error:", str(e))
            answer_text = "The medical reasoning model encountered an error and could not generate a response."

        # Warnings logic
        if safety.needs_handoff or safety.risk_level == "high":
            warnings = (
                "⚠️ This may represent a high-risk situation. "
                "The user should urgently consult a doctor or pharmacist in person."
            )
        elif safety.risk_level == "medium":
            warnings = (
                "⚠️ This topic involves medication safety. "
                "Recommend the user confirm with a clinician before acting."
            )
        else:
            warnings = (
                "ℹ️ This information is educational only and does not replace professional medical advice."
            )

        return MedicalAnswer(
            canonical_answer=answer_text,
            warnings=warnings,
            citations=citations,
            evidence=evidence_items,
        )
