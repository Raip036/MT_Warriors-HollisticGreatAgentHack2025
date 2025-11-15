from input_classifier import InputClassifier
from safety_advisor import SafetyAdvisor
from agent import PharmacyAgent, load_environment

def main():
    if not load_environment():
        print("❌ Missing environment variables")
        return

    classifier = InputClassifier()
    safety = SafetyAdvisor()
    pharmacy = PharmacyAgent()

    print("💬 Multi-Agent Pharmacy Session")
    print("Type 'exit' to quit")

    while True:
        user_input = input("❓ Your question: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break

        # Step 1: Classify intent & query type
        if not classifier.is_safe(user_input):
            print("⚠️ Input potentially unsafe or prompt injection. Try again.")
            continue
        query_type = classifier.classify_query_type(user_input)
        print(f"📝 Detected query type: {query_type}")

        # Step 2: Safety assessment
        print(safety.get_risk_message(user_input))
        if not safety.is_safe(user_input):
            continue

        # Step 3: Send safe input to PharmacyAgent
        response = pharmacy.ask(user_input)
        print(f"💬 Pharmacy Response: {response}")

if __name__ == "__main__":
    main()
