# backend/agents/orchestrator.py

import os
from dotenv import load_dotenv

from agents.input_classifier import InputClassifier
from agents.safety_advisor import SafetyAdvisor, SafetyAssessment
from agents.medical_reasoning_agent import MedicalReasoningAgent, MedicalAnswer
from agents.pharma_miku_agent import PharmaMikuAgent, UserFacingAnswer
from agents.judge import JudgeAgent, JudgeVerdict
from agents.trace_explainer import TraceExplainerAgent, TraceExplanation


# Load .env from backend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Orchestrator:
    """
    Controls the full multi-agent pipeline:
      1. Input classification
      2. Safety evaluation
      3. Medical reasoning (LLM + Valyu)
      4. Persona wrapping (PharmaMiku)
      5. Judge Agent (final safety check)
      6. Trace Explainer (glass box reasoning)
    """

    def __init__(self):
        self.agent1 = InputClassifier()
        self.agent2 = SafetyAdvisor()
        self.agent3 = MedicalReasoningAgent()
        self.agent4 = PharmaMikuAgent()
        self.agent5 = JudgeAgent()
        self.agent6 = TraceExplainerAgent()

        print("✨ Orchestrator initialised (Agent1 → Agent6)")

    # ============================================================
    # MAIN PIPELINE
    # ============================================================
    def run(self, user_input: str, progress_callback=None):
        """Run the pipeline with optional progress callback."""
        return self.run_with_progress(user_input, progress_callback)
    
    def run_with_progress(self, user_input: str, progress_callback=None):
        """Run the pipeline with progress updates."""
        trace = {}
        
        def progress(stage: str, message: str):
            if progress_callback:
                progress_callback(stage, message)

        # ------------------------------------------------------------
        # 1️⃣ INPUT CLASSIFIER
        # ------------------------------------------------------------
        progress("classifying", "pharmamiku is identifying the problem…")
        classification = self.agent1.classify_input(user_input)
        trace["input_classifier"] = classification.model_dump()
        age_group = classification.age_group if hasattr(classification, "age_group") else "unknown"

        # ------------------------------------------------------------
        # 2️⃣ SAFETY EVALUATION
        # ------------------------------------------------------------
        progress("safety", "pharmamiku is assessing safety…")
        safety = self.agent2.evaluate_risk(
            user_input=user_input,
            classification=classification
        )
        trace["safety_advisor"] = safety.model_dump()

        # Early stop: only block truly dangerous situations
        # Allow MEDIUM risk questions (like drug interactions) to proceed with warnings
        if safety.risk_level == "high" and safety.needs_handoff:
            progress("finalising", "pharmamiku is finalising answer…")
            final = (
                "⚠️ This may be a serious medical situation. "
                "Please seek professional medical help immediately."
            )
            trace["final_answer"] = final
            trace["safety_decision"] = "BLOCK"
            
            # Still run trace explainer for blocked requests
            try:
                trace_explanation = self.agent6.explain(
                    trace=trace,
                    user_message=user_input,
                    final_answer=final
                )
                trace["trace_explanation"] = trace_explanation.model_dump()
                
                # Append reasoning explanation
                reasoning_explanation = trace_explanation.trace_explanation_user_friendly
                if reasoning_explanation and reasoning_explanation.strip():
                    final = final + f"\n\n---\n\n💭 Why I'm saying this:\n{reasoning_explanation}"
            except Exception as e:
                trace["trace_explainer_error"] = str(e)
            
            return final, trace

        # ------------------------------------------------------------
        # 3️⃣ MEDICAL REASONING AGENT
        # ------------------------------------------------------------
        try:
            progress("researching", "pharmamiku is researching…")
            medical_answer: MedicalAnswer = self.agent3.run(
                user_input=user_input,
                classification=classification,
                safety=safety
            )
            trace["medical_reasoning"] = medical_answer.model_dump()

        except Exception as e:
            # Fail-safe: If Bedrock OR Valyu crashes
            progress("finalising", "pharmamiku is finalising answer…")
            fallback = (
                "⚠️ I had trouble generating a full medical explanation. "
                "Please consult a pharmacist or healthcare provider for accurate guidance."
            )
            trace["medical_reasoning_error"] = str(e)
            trace["final_answer"] = fallback
            
            # Still run trace explainer
            try:
                trace_explanation = self.agent6.explain(
                    trace=trace,
                    user_message=user_input,
                    final_answer=fallback
                )
                trace["trace_explanation"] = trace_explanation.model_dump()
                
                # Append reasoning explanation
                reasoning_explanation = trace_explanation.trace_explanation_user_friendly
                if reasoning_explanation and reasoning_explanation.strip():
                    fallback = fallback + f"\n\n---\n\n💭 What happened:\n{reasoning_explanation}"
            except Exception as e2:
                trace["trace_explainer_error"] = str(e2)
            
            return fallback, trace

        # ------------------------------------------------------------
        # 4️⃣ PHARMA MIKU PERSONA LAYER
        # ------------------------------------------------------------
        try:
            progress("thinking", "pharmamiku is thinking…")
            user_facing_answer = self.agent4.run(
                user_input=user_input,
                medical_answer=medical_answer,
                safety=safety,
                age_group=age_group if age_group != "unknown" else "adult"
            )
            trace["pharma_miku"] = user_facing_answer.model_dump()

        except Exception as e:
            progress("finalising", "pharmamiku is finalising answer…")
            backup = (
                "Here is the medical information, but I could not apply the persona layer."
            )
            trace["pharma_miku_error"] = str(e)
            trace["final_answer"] = backup
            
            # Still run trace explainer
            try:
                trace_explanation = self.agent6.explain(
                    trace=trace,
                    user_message=user_input,
                    final_answer=backup
                )
                trace["trace_explanation"] = trace_explanation.model_dump()
                
                # Append reasoning explanation
                reasoning_explanation = trace_explanation.trace_explanation_user_friendly
                if reasoning_explanation and reasoning_explanation.strip():
                    backup = backup + f"\n\n---\n\n💭 What happened:\n{reasoning_explanation}"
            except Exception as e2:
                trace["trace_explainer_error"] = str(e2)
            
            return backup, trace

        # ------------------------------------------------------------
        # 5️⃣ JUDGE AGENT (Final Safety & Quality Check)
        # ------------------------------------------------------------
        try:
            progress("judging", "pharmamiku is judging…")
            judge_verdict = self.agent5.evaluate(
                user_message=user_input,
                user_facing_answer=user_facing_answer,
                canonical_medical_answer=medical_answer,
                risk_level=safety.risk_level,
                safety_decision="ALLOW",  # We got past the early stop, so it's ALLOW
                needs_handoff=safety.needs_handoff
            )
            trace["judge"] = judge_verdict.model_dump()

            # Apply verdict (may adjust the answer)
            final_answer = self.agent5.apply_verdict(judge_verdict, user_facing_answer)
            trace["final_answer"] = final_answer.text
            trace["citations"] = final_answer.citations

        except Exception as e:
            # If judge fails, use the original answer
            print(f"❗ Judge Agent error: {e}")
            trace["judge_error"] = str(e)
            final_answer = user_facing_answer
            trace["final_answer"] = final_answer.text
            trace["citations"] = final_answer.citations

        # ------------------------------------------------------------
        # 6️⃣ TRACE EXPLAINER (Glass Box Reasoning)
        # ------------------------------------------------------------
        try:
            progress("finalising", "pharmamiku is finalising answer…")
            trace_explanation = self.agent6.explain(
                trace=trace,
                user_message=user_input,
                final_answer=final_answer.text
            )
            trace["trace_explanation"] = trace_explanation.model_dump()
            
            # Append human-interpretable reasoning explanation to the final answer
            reasoning_explanation = trace_explanation.trace_explanation_user_friendly
            if reasoning_explanation and reasoning_explanation.strip():
                # Format the reasoning explanation nicely
                formatted_reasoning = f"\n\n---\n\n💭 How I found this information:\n{reasoning_explanation}"
                final_answer_text = final_answer.text + formatted_reasoning
            else:
                final_answer_text = final_answer.text

        except Exception as e:
            print(f"❗ Trace Explainer error: {e}")
            trace["trace_explainer_error"] = str(e)
            final_answer_text = final_answer.text

        # Done! Return answer text (with reasoning) and trace (which includes citations)
        return final_answer_text, trace

