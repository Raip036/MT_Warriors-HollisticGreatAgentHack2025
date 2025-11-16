# backend/agents/agent.py

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# ============================================
# Load .env
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    print("⚠️ WARNING: .env not found:", ENV_PATH)


# ============================================
# Bedrock-Compatible Chat Wrapper
# ============================================
class HolisticAIBedrockChat:
    """
    A wrapper that converts normal messages into Amazon Bedrock
    Claude 3.x-compliant schema.
    """

    def __init__(self, model_name="anthropic.claude-3-5-sonnet-20241022-v2:0"):
        self.model_name = model_name
        self.api_url = os.getenv("HOLISTIC_AI_API_URL")
        self.api_token = os.getenv("HOLISTIC_AI_API_TOKEN")
        self.team_id = os.getenv("HOLISTIC_AI_TEAM_ID")

        if not self.api_url or not self.api_token or not self.team_id:
            print("⚠️ HolisticAIBedrockChat: MOCK MODE (missing credentials)")
            self.mock_mode = True
        else:
            self.mock_mode = False
            print("🧩 HolisticAIBedrockChat: REAL Bedrock mode enabled")

    # -----------------------------------------------------
    # Bedrock-compatible invocation
    # -----------------------------------------------------
    def invoke(self, messages):
        """
        Accepts:
        - A list of messages [{"role": "...", "content": "..."}]
        - Or a single string

        Converts to Bedrock-native schema:
        {"messages":[{"role":"user","content":[{"text":"..."}]}]}
        """

        # MOCK MODE
        if self.mock_mode:
            return "(MOCK RESPONSE) — LLM disabled."

        # ----------------------------------------
        # Convert input into a single Bedrock message
        # ----------------------------------------
        if isinstance(messages, str):
            combined_text = messages

        elif isinstance(messages, list):
            # Bedrock does NOT support "system" role.
            # We turn EVERYTHING into a single user message.
            text_blocks = []
            for m in messages:
                txt = m.get("content", "")
                if isinstance(txt, list):
                    txt = " ".join([x.get("text", "") for x in txt])
                text_blocks.append(str(txt))
            combined_text = "\n\n".join(text_blocks)

        else:
            raise ValueError("Invalid message format passed to invoke()")

        bedrock_body = {
            "team_id": self.team_id,
            "api_token": self.api_token,
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": combined_text}
                    ]
                }
            ],
            "max_tokens": 1024
        }

        headers = {
            "Content-Type": "application/json",
            "X-Api-Token": self.api_token,
        }

        # ----------------------------------------
        # Make request to Bedrock-proxy API
        # ----------------------------------------
        response = requests.post(
            self.api_url,
            headers=headers,
            data=json.dumps(bedrock_body),
            timeout=60
        )

        print("🔍 Bedrock Status:", response.status_code)
        print("🔍 Bedrock Raw:", response.text)

        response.raise_for_status()
        data = response.json()

        # Bedrock response shapes vary; handle multiple
        if "completion" in data:
            return data["completion"]

        if "output" in data and isinstance(data["output"], str):
            return data["output"]

        if "content" in data:
            # Claude returns list of content blocks
            try:
                return data["content"][0]["text"]
            except:
                pass

        # Fallback
        return str(data)


# ============================================
# Factory
# ============================================
def get_chat_model():
    return HolisticAIBedrockChat()


# ============================================
# Removed unsafe roles from legacy PharmacyAgent
# ============================================
class PharmacyAgent:
    """
    SAFE version — no system role, Bedrock-compatible.
    """

    def __init__(self):
        self.llm = get_chat_model()

    def ask(self, question: str) -> str:
        prompt = (
            "You are a friendly pharmacy assistant. "
            "Provide general drug information only. "
            "Do NOT diagnose. "
            "Always encourage speaking with a doctor if unsure.\n\n"
            f"User question: {question}"
        )
        return self.llm.invoke(prompt)
