# backend/test_orchestrator.py

import sys
import os

# --------------------------------------------
# Ensure Python can find the "agents" package
# --------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(CURRENT_DIR)
sys.path.append(PARENT_DIR)

# --------------------------------------------
# Load environment variables (for API keys)
# --------------------------------------------
from dotenv import load_dotenv
load_dotenv(os.path.join(PARENT_DIR, ".env"))

# --------------------------------------------
# Import the orchestrator
# --------------------------------------------
from agents.orchestrator import Orchestrator


def main():
    print("🚀 Running Orchestrator Test...\n")

    orch = Orchestrator()

    user_input = "Can I take ibuprofen with paracetamol?"

    final, trace = orch.run(user_input)

    print("\n===== FINAL ANSWER =====")
    print(final)

    print("\n===== TRACE OUTPUT =====")
    for k, v in trace.items():
        print(f"{k} → {v}")

if __name__ == "__main__":
    main()

