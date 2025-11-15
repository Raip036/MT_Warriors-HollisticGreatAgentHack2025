from agents.input_classifier import InputClassifier
from agents.safety_advisor import SafetyAdvisor
from agents.agent import PharmacyAgent, load_environment

def main():
    if not load_environment():
        print("❌ Missing environment variables")
        return

    # Initialize agents
    classifier = InputClassifier()
    safety = SafetyAdvisor()
    pharmacy = PharmacyAgent()

    print("\n💬 Multi-Agent Pharmacy Session")
    print("Type 'exit' to quit\n")

    while True:
        user_input = input("❓ Your question: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("👋 Exiting session. Stay safe!")
            break
        if not user_input:
            print("⚠️ Please enter a valid question.\n")
            continue

        print("\n==============================")
        print("📝 Step 1: Classify Input")

        # Step 1: Classify intent & query type
        if not classifier.is_safe(user_input):
            print("⚠️ Input potentially unsafe or prompt injection. Try again.\n")
            continue

        query_type = classifier.classify_query_type(user_input)
        classification = classifier.classify_input(user_input)

        print(f"💡 Detected Query Type: {query_type}")
        print(f"🧠 Intent: {classification.intent}")
        print(f"⚠️ Risk Level: {classification.risk_level}")
        print(f"📞 Needs Handoff: {classification.needs_handoff}")
        print(f"🔍 Explanation: {classification.explanation}")

        # Step 2: Safety assessment using LLM
        print("\n==============================")
        print("🛡️ Step 2: Safety Assessment")

        assessment = safety.evaluate_risk(user_input)
        print(f"⚠️ Risk: {assessment.risk_level.upper()}")
        print(f"📞 Needs Handoff: {assessment.needs_handoff}")
        print(f"🔍 Explanation: {assessment.explanation}")
        print(f"📝 Summary: {getattr(assessment, 'summary', 'No summary available')}")
        
        # Skip unsafe input
        if assessment.risk_level.lower() == "high":
            print("\n❌ High-risk input detected. Skipping Pharmacy response.\n")
            continue

        # Step 3: Send safe input to PharmacyAgent
        print("\n==============================")
        print("💊 Step 3: Pharmacy Response")
        response = pharmacy.ask(user_input)
        print(f"💬 Response:\n{response}\n")
        print("==============================\n")

if __name__ == "__main__":
    main()
