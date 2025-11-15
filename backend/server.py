from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agents.input_classifier import InputClassifier
from agents.safety_advisor import SafetyAdvisor
from agents.agent import PharmacyAgent, load_environment


# ---------------------------
# FastAPI setup
# ---------------------------
app = FastAPI()

# Enable CORS for your frontend
origins = [
    "http://localhost:3000",  # Next.js dev server
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Initialize agents
# ---------------------------
if not load_environment():
    raise RuntimeError("❌ Missing environment variables")

classifier = InputClassifier()
safety = SafetyAdvisor()
pharmacy = PharmacyAgent()

# ---------------------------
# Request model
# ---------------------------
class ChatRequest(BaseModel):
    text: str

# ---------------------------
# Chat endpoint
# ---------------------------
@app.post("/ask")
async def ask(request: ChatRequest):
    user_input = request.text.strip()
    if not user_input:
        raise HTTPException(status_code=400, detail="Empty input")

    # Step 1: Classify input
    classification = classifier.classify_input(user_input)

    # Step 2: Safety check via LLM
    assessment = safety.evaluate_risk(user_input)

    # Step 3: Decide if we proceed
    if assessment.risk_level.lower() == "high":
        # Optional: you can still check if this is allowed
        return {
            "error": "High risk input. Cannot provide pharmacy advice.",
            "assessment": assessment.dict()
        }

    # Step 4: Generate response via PharmacyAgent
    response = pharmacy.ask(user_input)

    return {
        "user_input": user_input,
        "classification": classification.dict(),
        "assessment": assessment.dict(),
        "response": response
    }
