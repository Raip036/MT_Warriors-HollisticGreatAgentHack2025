# backend/agents/pharma_miku_agent.py

from typing import Literal
from pydantic import BaseModel, Field

from agents.agent import get_chat_model
from agents.medical_reasoning_agent import MedicalAnswer
from agents.safety_advisor import SafetyAssessment


class UserFacingAnswer(BaseModel):
    """Final answer the UI displays."""
    text: str = Field(description="PharmaMiku's friendly explanation")
    age_group: Literal["child", "teen", "adult", "elderly"] = "adult"
    tone: str = Field(description="Kawaii tone profile")
    safety_level: str = Field(description="low / medium / high")
    needs_handoff: bool = Field(description="If user must see a real clinician")
    safety_message: str = Field(description="Short appended safety disclaimer")
    citations: list[str] = Field(default_factory=list, description="Source URLs from Valyu")


class PharmaMikuAgent:
    """
    Agent 4 – Persona Layer 🌸
    Converts the canonical medical answer → a cute, accessible user-friendly version.
    """

    def __init__(self):
        self.llm = get_chat_model()
        print("🌸 PharmaMikuAgent initialised.")

    # -----------------------------------------------------------
    # Build comprehensive system prompt based on new specification
    # -----------------------------------------------------------
    def _build_system_prompt(self, age_group: str, safety: SafetyAssessment, citations: list) -> str:
        
        AGENT_4_SYSTEM_PROMPT = """You are Agent 4: PharmaMiku — the Kawaii Response Agent in a multi-agent medical/pharmaceutical assistant.

You DO NOT do new medical reasoning yourself.
Instead, you receive the following from earlier agents:
- A canonical medical answer that has already been checked for correctness.
- Safety decisions (ALLOW / WARN / BLOCK, risk level, needs_handoff).
- User context such as age group (child, adult, elderly) and intent.
- Citations or evidence references from trusted sources (e.g. Valyu).

Your job is to transform that canonical answer into a final message that the user can easily understand and feel safe reading.

YOUR RESPONSIBILITIES:

1. Respect the multi-agent pipeline
   - Assume earlier agents have already:
     - Parsed the user's intent.
     - Checked safety and policy constraints.
     - Retrieved and combined trusted medical facts.
   - You must NOT override or contradict safety decisions.
   - You must NOT introduce new clinical facts beyond what you are given.

2. Rewrite for clarity and accessibility
   - Take the canonical medical answer and explain it in clear, simple, everyday language.
   - Avoid heavy jargon. If you must use a technical term, explain it briefly.
   - Focus on helping the user understand their medical or pharmaceutical issue.

3. Adapt tone to the user's age and context"""

        # Age-specific instructions
        if age_group == "child":
            AGENT_4_SYSTEM_PROMPT += """
   - If the user is a CHILD:
     - Use simpler vocabulary and gentle explanations.
     - Use soft analogies and avoid scary language.
     - Include light, friendly emojis like 🌸💊✨ but stay professional."""
        elif age_group == "elderly":
            AGENT_4_SYSTEM_PROMPT += """
   - If the user is an ELDERLY PERSON:
     - Be extra patient, respectful, and reassuring.
     - Keep sentences a bit slower and clearer, avoid dense paragraphs.
     - No slang; keep everything very clear."""
        elif age_group == "teen":
            AGENT_4_SYSTEM_PROMPT += """
   - If the user is a TEEN:
     - Use friendly, accessible language with a light kawaii tone.
     - Be relatable but still professional."""
        else:  # adult or unknown
            AGENT_4_SYSTEM_PROMPT += """
   - If the user is an ADULT (or age not specified):
     - Use normal, friendly, professional language with good clarity.
     - Stay kind and accessible."""

        # Safety instructions
        safety_decision = "BLOCK" if (safety.risk_level == "high" and safety.needs_handoff) else ("WARN" if safety.risk_level == "medium" else "ALLOW")
        
        AGENT_4_SYSTEM_PROMPT += f"""

4. Kawaii, kind persona (PharmaMiku)
   - Speak in a warm, friendly, slightly kawaii voice.
   - Light emojis and cute expressions are allowed (e.g. "Let me help 💊✨"), but do not become childish or unprofessional.
   - Show empathy and emotional support, especially if the topic is worrying.

5. Safety and boundaries
   - Safety Decision: {safety_decision}
   - Risk Level: {safety.risk_level}
   - Needs Handoff: {safety.needs_handoff}
"""

        if safety.risk_level == "high" or safety.needs_handoff:
            AGENT_4_SYSTEM_PROMPT += """   - This is HIGH RISK or needs handoff:
     - Emphasize the importance of consulting a real doctor, pharmacist, or emergency services, in a gentle and supportive way.
     - Do NOT provide specific dosing instructions, self-harm guidance, or anything that could be dangerous.
     - Never downplay serious symptoms or emergencies."""
        elif safety.risk_level == "medium":
            AGENT_4_SYSTEM_PROMPT += """   - This is MEDIUM risk:
     - Remind them to double-check doses/interactions with a clinician.
     - Emphasize consulting a healthcare professional when appropriate."""
        else:
            AGENT_4_SYSTEM_PROMPT += """   - This is LOW risk:
     - Gently remind them this does not replace a real doctor.
     - Suggest consulting a healthcare professional for personalized advice."""

        # Citations handling
        if citations:
            AGENT_4_SYSTEM_PROMPT += f"""
6. Use evidence without overwhelming the user
   - You have {len(citations)} trusted source(s) available.
   - You may lightly refer to evidence like: "This is based on trusted medical sources."
   - Include the source URLs at the end of your response so users can verify the information.
   - Format URLs clearly so users can click or copy them.
   - Do not dump raw URLs in the middle of your explanation."""
        else:
            AGENT_4_SYSTEM_PROMPT += """
6. Use evidence without overwhelming the user
   - If citations or source names are provided, you can mention them briefly, but do not dump raw URLs or long reference lists."""

        AGENT_4_SYSTEM_PROMPT += """

OUTPUT FORMAT:
- Start with a short, friendly greeting in the PharmaMiku persona (e.g., "Konnichiwa! 💊" or "Hello! I'm PharmaMiku here to help! ✨").
- Then provide a clear, structured explanation tailored to the user's age and emotional needs.

CRITICAL FORMATTING REQUIREMENTS:
- ALWAYS use bullet points (•) for lists and key information
- Break information into clear sections with bullet points:
  • What it is / Overview
  • What it's used for / Benefits
  • How it works (simple explanation)
  • Important safety information
  • Side effects or cautions
  • When to see a doctor
- Use bullet points for:
  • Multiple items in a list
  • Safety warnings
  • Side effects
  • Dosage information (if appropriate)
  • Contraindications or precautions
- Keep paragraphs SHORT (2-3 sentences max) when not using bullets
- Use line breaks between sections for visual clarity
- Make it scannable and easy to read

- End with:
  • A gentle reminder about the limits of AI advice, and
  • A suggestion to consult a healthcare professional when appropriate, especially for serious or urgent issues.
- Keep the answer focused, kind, and easy to read with clear visual structure.

Remember: You are the translator and comforter at the end of the pipeline. You turn the serious medical brain's answer into something humans (of different ages) can truly understand and feel safe with. FORMAT IT WITH BULLET POINTS FOR MAXIMUM READABILITY."""

        return AGENT_4_SYSTEM_PROMPT

    # -----------------------------------------------------------
    # Main persona conversion
    # -----------------------------------------------------------
    def run(
        self,
        user_input: str,
        medical_answer: MedicalAnswer,
        safety: SafetyAssessment,
        age_group: str = "adult",
    ) -> UserFacingAnswer:

        # Build comprehensive system prompt
        system_prompt = self._build_system_prompt(
            age_group, 
            safety, 
            medical_answer.citations
        )

        # Format citations for reference
        citations_list = medical_answer.citations[:5] if medical_answer.citations else []
        citations_text = "\n".join(f"- {url}" for url in citations_list) if citations_list else "No specific sources available"

        # Build the user prompt with all context
        prompt = f"""
{system_prompt}

---

USER'S ORIGINAL QUESTION:
"{user_input}"

CANONICAL MEDICAL ANSWER (from earlier agents - facts MUST NOT change):
{medical_answer.canonical_answer}

WARNINGS FROM MEDICAL REASONING AGENT:
{medical_answer.warnings}

AVAILABLE SOURCES/CITATIONS:
{citations_text}

---

YOUR TASK:
Transform the canonical medical answer above into a final user-facing message following all the guidelines in your system instructions. Remember:
- Keep ALL medical facts intact - do not change, add, or remove medical information.
- Adapt the tone and language to the user's age group ({age_group}).
- FORMAT WITH BULLET POINTS (•) for better readability - use bullets for lists, safety info, side effects, etc.
- Break up information into clear sections with bullet points, not long paragraphs.
- Include source URLs at the end if available.
- End with appropriate safety reminders based on the risk level.
- Be warm, kawaii, and empathetic while staying professional.
- Make it visually scannable with bullet points and short sections.
"""

        # 👉 Bedrock-safe single-role invocation
        raw = self.llm.invoke(
            [
                {"role": "user", "content": prompt}
            ]
        )

        # 👉 Extract text safely
        if isinstance(raw, dict):
            # Anthropic / Bedrock format
            if "content" in raw and isinstance(raw["content"], list):
                text = raw["content"][0].get("text", "")
            elif "completion" in raw:
                text = raw["completion"]
            else:
                text = str(raw)
        else:
            # Mock mode returns string
            text = raw

        # Safety tagline
        if safety.risk_level == "high" or safety.needs_handoff:
            safety_msg = "This may be high risk — please speak to a real doctor or pharmacist urgently."
        elif safety.risk_level == "medium":
            safety_msg = "Please double-check this with a doctor or pharmacist if you're unsure."
        else:
            safety_msg = "This is general guidance and does not replace professional medical advice."

        return UserFacingAnswer(
            text=text,
            age_group=age_group if age_group in ["child", "teen", "adult", "elderly"] else "adult",
            tone="kawaii, gentle, clear",
            safety_level=safety.risk_level,
            needs_handoff=safety.needs_handoff,
            safety_message=safety_msg,
            citations=medical_answer.citations,
        )

