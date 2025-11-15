#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Input Classifier Agent for PharmaMiku

- Loads Holistic AI Bedrock / OpenAI credentials from environment or .env
- Uses get_chat_model from holistic_ai_bedrock
- Defines a Pydantic schema for classification
- Wraps the LLM with structured output
- Provides:
    - classify_input(user_message: str) -> InputClassification
    - a small demo in main() to test it
"""

# ============================================
# Standard library imports
# ============================================
import os
import time
import json
import random
from pathlib import Path

# ============================================
# Third-party imports (as per tutorial)
# ============================================
from dotenv import load_dotenv

# Import from core module (Holistic AI Bedrock helper)
try:
    import sys
    # Ensure current directory is on path (if needed)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from holistic_ai_bedrock import HolisticAIBedrockChat, get_chat_model
    HOLISTIC_AVAILABLE = True
    print("✅ Holistic AI Bedrock helper function loaded")
except ImportError:
    HOLISTIC_AVAILABLE = False
    print("⚠️  Could not import holistic_ai_bedrock - will use OpenAI only (if key set)")

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from datasets import load_dataset
from tqdm import tqdm
import numpy as np

# ============================================
# Load environment variables
# ============================================
env_path = Path('../.env')
if env_path.exists():
    load_dotenv(env_path)
    print("📄 Loaded configuration from .env file")
else:
    print("⚠️  No .env file found - using environment variables or hardcoded keys")

print("\n🔑 API Key Status:")
if os.getenv('HOLISTIC_AI_TEAM_ID') and os.getenv('HOLISTIC_AI_API_TOKEN'):
    print("  ✅ Holistic AI Bedrock credentials loaded (will use Bedrock)")
elif os.getenv('OPENAI_API_KEY'):
    print("  ⚠️  OpenAI API key loaded (Bedrock credentials not set)")
    print("     💡 Tip: Set HOLISTIC_AI_TEAM_ID and HOLISTIC_AI_API_TOKEN to use Bedrock (recommended)")
else:
    print("  ⚠️  No API keys found")
    print("     Set Holistic AI Bedrock credentials (recommended) or OpenAI key")

print("\n✅ All imports successful!\n")


# ============================================
# Pydantic model: InputClassification
# ============================================

class InputClassification(BaseModel):
    """
    How PharmaMiku should interpret the user’s message.
    """

    intent: str = Field(
        description=(
            "Primary intent of the user’s message. "
            "Must be one of: "
            "[drug_information, dosage_question, side_effects, "
            "drug_interaction, symptom_check, emergency_or_crisis, "
            "general_health, other]."
        )
    )

    risk_level: str = Field(
        description=(
            "Rough safety risk of answering this directly. "
            "Must be one of: [low, medium, high]."
        )
    )

    needs_handoff: bool = Field(
        description=(
            "True if this should be escalated / refused and redirected "
            "to a doctor, pharmacist, or emergency services."
        )
    )

    explanation: str = Field(
        description="Short natural language explanation of why you classified it this way."
    )


# ============================================
# Create base chat model and structured classifier
# ============================================

base_llm = None
classifier_llm = None

if os.getenv('HOLISTIC_AI_TEAM_ID') and os.getenv('HOLISTIC_AI_API_TOKEN') and HOLISTIC_AVAILABLE:
    # Recommended: Bedrock via Holistic AI
    base_llm = get_chat_model("claude-3-5-sonnet")
    print("🤖 Using Bedrock model: claude-3-5-sonnet for input classification")
elif os.getenv('OPENAI_API_KEY'):
    # Fallback: OpenAI via same helper (as in tutorials)
    base_llm = get_chat_model("gpt-4o-mini")
    print("🤖 Using OpenAI model: gpt-4o-mini for input classification")
else:
    print("❌ No model configured for input classifier (no API keys).")

if base_llm is not None:
    classifier_llm = base_llm.with_structured_output(InputClassification)
    print("✅ Structured output classifier is ready\n")
else:
    print("⚠️ classifier_llm is None - classification will fail until keys are set.\n")


# ============================================
# Classifier agent function
# ============================================

def classify_input(user_message: str) -> InputClassification:
    """
    Simple input classifier agent.

    Takes a raw user message and returns an InputClassification object
    produced by the LLM via structured output.
    """

    if classifier_llm is None:
        raise RuntimeError(
            "No LLM configured. "
            "Set HOLISTIC_AI_TEAM_ID and HOLISTIC_AI_API_TOKEN (recommended) "
            "or OPENAI_API_KEY."
        )

    prompt = (
        "You are an input classifier for a medicine & health assistant.\n"
        "Given the user's message, you must fill in this JSON schema:\n\n"
        "intent: one of [drug_information, dosage_question, side_effects, "
        "drug_interaction, symptom_check, emergency_or_crisis, general_health, other]\n"
        "risk_level: one of [low, medium, high]\n"
        "needs_handoff: true or false (true if the user should be told to see "
        "a doctor, pharmacist, or emergency services)\n"
        "explanation: brief reasoning.\n\n"
        "Be conservative: anything suggesting self-harm, overdose, "
        "severe or sudden symptoms, or medical emergencies should have "
        "risk_level = high and needs_handoff = true.\n\n"
        f"User message:\n```{user_message}```"
    )

    # Directly invoke with a string prompt – no extra libraries
    result = classifier_llm.invoke(prompt)

    # result is an InputClassification instance
    return result


# ============================================
# Demo / CLI entry point
# ============================================

def run_demo():
    """
    Runs a small demo using a few test messages,
    then allows interactive input from stdin.
    """

    if classifier_llm is None:
        print("❌ Cannot run demo: classifier_llm is not initialized.")
        return

    print("======================================")
    print("🔬 Input Classifier Agent Demo (PharmaMiku)")
    print("======================================\n")

    # Some fixed test messages
    test_messages = [
        "Can I take ibuprofen together with paracetamol?",
        "My grandma is having chest pain and trouble breathing, what should I do?",
        "What are the common side effects of metformin?",
        "I've been a bit tired lately, how can I improve my energy?",
        "If I take double my dose of antidepressants, will it work faster?",
    ]

    for msg in test_messages:
        print("\n------------------------------")
        print("💬 User:", msg)
        classification = classify_input(msg)
        print("🧠 intent:       ", classification.intent)
        print("⚠️ risk_level:   ", classification.risk_level)
        print("📞 needs_handoff:", classification.needs_handoff)
        print("🔍 explanation:  ", classification.explanation)

    print("\n======================================")
    print("💻 Interactive mode (type 'exit' to quit)")
    print("======================================\n")

    while True:
        try:
            user_msg = input("You: ").strip()
        except EOFError:
            print("\n👋 EOF received, exiting.")
            break

        if not user_msg:
            continue
        if user_msg.lower() in ("exit", "quit"):
            print("👋 Goodbye!")
            break

        try:
            classification = classify_input(user_msg)
        except Exception as e:
            print("❌ Error during classification:", str(e))
            continue

        print("🧠 intent:       ", classification.intent)
        print("⚠️ risk_level:   ", classification.risk_level)
        print("📞 needs_handoff:", classification.needs_handoff)
        print("🔍 explanation:  ", classification.explanation)
        print()


if __name__ == "__main__":
    run_demo()