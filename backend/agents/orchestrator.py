# backend/agents/orchestrator.py

import os
import time
import uuid
from dotenv import load_dotenv

from agents.input_classifier import InputClassifier
from agents.safety_advisor import SafetyAdvisor, SafetyAssessment
from agents.medical_reasoning_agent import MedicalReasoningAgent, MedicalAnswer
from agents.pharma_miku_agent import PharmaMikuAgent, UserFacingAnswer
from agents.judge import JudgeAgent, JudgeVerdict
from agents.trace_explainer import TraceExplainerAgent, TraceExplanation
from agents.tool_decision_agent import ToolDecisionAgent
from observability import get_trace_manager, StepType
from tools import (
    get_tool_manager,
    CalculatorTool,
    DrugInfoTool,
    ReminderTool,
    SummarizerTool,
)


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
        self.tool_decision_agent = ToolDecisionAgent()
        self.trace_manager = get_trace_manager()
        self.tool_manager = get_tool_manager()
        
        # Register all tools
        self._register_tools()

        print("✨ Orchestrator initialised (Agent1 → Agent6 + Tool System)")
    
    def _register_tools(self):
        """Register all available tools."""
        self.tool_manager.register_tool(CalculatorTool())
        self.tool_manager.register_tool(DrugInfoTool())
        self.tool_manager.register_tool(ReminderTool())
        self.tool_manager.register_tool(SummarizerTool())
        print(f"✅ Registered {len(self.tool_manager.tools)} tools")

    # ============================================================
    # MAIN PIPELINE
    # ============================================================
    def run(self, user_input: str, progress_callback=None):
        """Run the pipeline with optional progress callback."""
        return self.run_with_progress(user_input, progress_callback)
    
    def run_with_progress(self, user_input: str, progress_callback=None, session_id: str = None):
        """Run the pipeline with progress updates and full traceability."""
        # Start trace session
        if session_id is None:
            session_id = str(uuid.uuid4())
        self.trace_manager.start_trace(session_id)
        
        # Legacy trace dict for backward compatibility
        trace = {}
        trace["session_id"] = session_id
        
        def progress(stage: str, message: str):
            if progress_callback:
                progress_callback(stage, message)

        # Track state
        current_state = {
            "user_input": user_input,
            "stage": "initialized"
        }

        # ------------------------------------------------------------
        # 1️⃣ INPUT CLASSIFIER
        # ------------------------------------------------------------
        progress("classifying", "pharmamiku is identifying the problem")
        
        # Log decision step: starting classification
        start_time = time.time()
        self.trace_manager.append_decision(
            session_id=session_id,
            input_state={"user_input": user_input, "stage": "classification"},
            reasoning="Starting input classification to understand user intent",
            selected_action="classify_input",
            metadata={"agent": "InputClassifier", "step": 1}
        )
        
        classification = self.agent1.classify_input(user_input)
        duration_ms = (time.time() - start_time) * 1000
        
        # Log tool call result (classification is like a tool)
        self.trace_manager.append_trace(
            session_id=session_id,
            step_type=StepType.TOOL_CALL,
            input_data={"user_input": user_input},
            output_data=classification.model_dump(),
            metadata={"agent": "InputClassifier", "duration_ms": duration_ms, "summary": f"Classified as: {classification.intent}"},
            tool_name="classify_input",
            duration_ms=duration_ms,
            success=True
        )
        
        trace["input_classifier"] = classification.model_dump()
        age_group = classification.age_group if hasattr(classification, "age_group") else "unknown"
        
        # Update state
        old_state = current_state.copy()
        current_state.update({
            "classification": classification.model_dump(),
            "age_group": age_group,
            "stage": "classified"
        })
        self.trace_manager.append_memory_update(
            session_id=session_id,
            old_state=old_state,
            new_state=current_state,
            cause="classification_result",
            metadata={"agent": "InputClassifier"}
        )

        # ------------------------------------------------------------
        # 2️⃣ SAFETY EVALUATION
        # ------------------------------------------------------------
        progress("safety", "pharmamiku is assessing safety")
        
        # Log decision step: starting safety evaluation
        start_time = time.time()
        self.trace_manager.append_decision(
            session_id=session_id,
            input_state={"user_input": user_input, "classification": classification.model_dump()},
            reasoning="Evaluating safety risk based on classification",
            selected_action="evaluate_risk",
            metadata={"agent": "SafetyAdvisor", "step": 2}
        )
        
        safety = self.agent2.evaluate_risk(
            user_input=user_input,
            classification=classification
        )
        duration_ms = (time.time() - start_time) * 1000
        
        # Log tool call result
        self.trace_manager.append_trace(
            session_id=session_id,
            step_type=StepType.TOOL_CALL,
            input_data={"user_input": user_input, "classification": classification.model_dump()},
            output_data=safety.model_dump(),
            metadata={"agent": "SafetyAdvisor", "duration_ms": duration_ms, "summary": f"Risk level: {safety.risk_level}"},
            tool_name="evaluate_risk",
            duration_ms=duration_ms,
            success=True
        )
        
        trace["safety_advisor"] = safety.model_dump()
        
        # Update state
        old_state = current_state.copy()
        current_state.update({
            "safety": safety.model_dump(),
            "stage": "safety_evaluated"
        })
        self.trace_manager.append_memory_update(
            session_id=session_id,
            old_state=old_state,
            new_state=current_state,
            cause="safety_evaluation_result",
            metadata={"agent": "SafetyAdvisor"}
        )

        # ------------------------------------------------------------
        # 2.5️⃣ TOOL EXECUTION (if needed)
        # ------------------------------------------------------------
        tool_results = []
        tool_context = {}
        
        # Decide if tools are needed
        progress("tool_decision", "pharmamiku is deciding which tools to use")
        start_time_tool_decision = time.time()
        
        self.trace_manager.append_decision(
            session_id=session_id,
            input_state={"user_input": user_input, "classification": classification.model_dump()},
            reasoning="Analyzing user request to determine if any tools should be called",
            selected_action="decide_tools",
            metadata={"agent": "ToolDecisionAgent", "step": 2.5}
        )
        
        tool_decision = self.tool_decision_agent.decide_tool(
            user_input,
            context={"classification": classification.model_dump(), "safety": safety.model_dump()}
        )
        decision_duration_ms = (time.time() - start_time_tool_decision) * 1000
        
        self.trace_manager.append_trace(
            session_id=session_id,
            step_type=StepType.DECISION,
            input_data={"user_input": user_input},
            output_data={
                "tool_decision": {
                    "tool_name": tool_decision.tool_name,
                    "arguments": tool_decision.arguments,
                    "reasoning": tool_decision.reasoning
                }
            },
            metadata={
                "agent": "ToolDecisionAgent",
                "duration_ms": decision_duration_ms,
                "summary": f"Decided to use tool: {tool_decision.tool_name or 'none'}"
            }
        )
        
        # Execute tools if needed (can chain multiple tools)
        if tool_decision.should_use_tool:
            progress("tool_execution", f"pharmamiku is using {tool_decision.tool_name}")
            
            import asyncio
            # Run async tool execution
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            tool_result = loop.run_until_complete(
                self.tool_manager.execute_tool(
                    tool_name=tool_decision.tool_name,
                    arguments=tool_decision.arguments,
                    session_id=session_id,
                    trace_manager=self.trace_manager
                )
            )
            
            tool_results.append({
                "tool_name": tool_decision.tool_name,
                "result": tool_result.output if tool_result.success else None,
                "error": tool_result.error,
                "success": tool_result.success
            })
            
            # If tool result contains text that needs summarization, chain summarizer
            if tool_result.success and tool_decision.tool_name == "drug_info":
                # Check if user asked for summary
                if "summarize" in user_input.lower() or "summary" in user_input.lower():
                    # Extract instructions text
                    drug_data = tool_result.output.get("data", {})
                    instructions = drug_data.get("instructions", "")
                    
                    if instructions:
                        progress("tool_execution", "pharmamiku is summarizing the instructions")
                        summarizer_result = loop.run_until_complete(
                            self.tool_manager.execute_tool(
                                tool_name="summarizer",
                                arguments={
                                    "text": instructions,
                                    "max_length": 100,
                                    "focus": "instructions"
                                },
                                session_id=session_id,
                                trace_manager=self.trace_manager
                            )
                        )
                        
                        tool_results.append({
                            "tool_name": "summarizer",
                            "result": summarizer_result.output if summarizer_result.success else None,
                            "error": summarizer_result.error,
                            "success": summarizer_result.success
                        })
            
            # Update state with tool results
            old_state = current_state.copy()
            current_state.update({
                "tool_results": tool_results,
                "stage": "tools_executed"
            })
            self.trace_manager.append_memory_update(
                session_id=session_id,
                old_state=old_state,
                new_state=current_state,
                cause="tool_execution_results",
                metadata={"tools_used": [r["tool_name"] for r in tool_results]}
            )
            
            # Add tool results to context for medical reasoning
            tool_context = {
                "tool_results": tool_results,
                "has_tool_data": any(r["success"] for r in tool_results)
            }
            trace["tool_results"] = tool_results

        # Early stop: only block truly dangerous situations
        # Allow MEDIUM risk questions (like drug interactions) to proceed with warnings
        if safety.risk_level == "high" and safety.needs_handoff:
            # Log decision: blocking due to high risk
            self.trace_manager.append_decision(
                session_id=session_id,
                input_state={"safety": safety.model_dump()},
                reasoning=f"High risk detected ({safety.risk_level}) with handoff required. Blocking request.",
                selected_action="BLOCK",
                metadata={"agent": "Orchestrator", "step": "early_stop", "reason": "high_risk"}
            )
            
            progress("finalising", "pharmamiku is finalising answer")
            final = (
                "💊 Hey there! I'm really concerned about what you've shared. "
                "This sounds like something that needs immediate attention from a healthcare professional. "
                "Please reach out to a doctor, pharmacist, or emergency services right away - they're the best people to help you with this! ✨"
            )
            trace["final_answer"] = final
            trace["safety_decision"] = "BLOCK"
            
            # Update state
            old_state = current_state.copy()
            current_state.update({
                "final_answer": final,
                "safety_decision": "BLOCK",
                "stage": "blocked"
            })
            self.trace_manager.append_memory_update(
                session_id=session_id,
                old_state=old_state,
                new_state=current_state,
                cause="safety_block",
                metadata={"agent": "Orchestrator"}
            )
            
            # Still run trace explainer for blocked requests
            try:
                start_time = time.time()
                trace_explanation = self.agent6.explain(
                    trace=trace,
                    user_message=user_input,
                    final_answer=final
                )
                duration_ms = (time.time() - start_time) * 1000
                
                self.trace_manager.append_trace(
                    session_id=session_id,
                    step_type=StepType.TOOL_CALL,
                    input_data={"trace": trace, "user_message": user_input, "final_answer": final},
                    output_data=trace_explanation.model_dump(),
                    metadata={"agent": "TraceExplainer", "duration_ms": duration_ms, "summary": "Generated trace explanation"},
                    tool_name="explain",
                    duration_ms=duration_ms,
                    success=True
                )
                
                trace["trace_explanation"] = trace_explanation.model_dump()
                
                # Append reasoning explanation
                reasoning_explanation = trace_explanation.trace_explanation_user_friendly
                if reasoning_explanation and reasoning_explanation.strip():
                    final = final + f"\n\n---\n\n💭 Why I'm saying this:\n{reasoning_explanation}"
            except Exception as e:
                trace["trace_explainer_error"] = str(e)
                self.trace_manager.append_trace(
                    session_id=session_id,
                    step_type=StepType.TOOL_CALL,
                    input_data={"trace": trace, "user_message": user_input, "final_answer": final},
                    output_data=None,
                    metadata={"agent": "TraceExplainer", "summary": "Trace explainer failed"},
                    tool_name="explain",
                    duration_ms=0,
                    success=False,
                    error=str(e)
                )
            
            # End trace
            structured_trace = self.trace_manager.end_trace(session_id)
            trace["structured_trace"] = structured_trace
            
            return final, trace

        # ------------------------------------------------------------
        # 3️⃣ MEDICAL REASONING AGENT
        # ------------------------------------------------------------
        try:
            progress("researching", "pharmamiku is researching")
            
            # Enhance user input with tool results if available
            enhanced_input = user_input
            if tool_context.get("has_tool_data"):
                tool_summary = "\n\nTool Results:\n"
                for tool_result in tool_results:
                    if tool_result["success"]:
                        tool_summary += f"- {tool_result['tool_name']}: {str(tool_result['result'])[:200]}\n"
                enhanced_input = user_input + tool_summary
            
            start_time_medical = time.time()
            medical_answer: MedicalAnswer = self.agent3.run(
                user_input=enhanced_input,
                classification=classification,
                safety=safety,
                session_id=session_id
            )
            duration_ms = (time.time() - start_time_medical) * 1000
            
            # Log tool call result (medical reasoning includes LLM + Valyu search)
            self.trace_manager.append_trace(
                session_id=session_id,
                step_type=StepType.TOOL_CALL,
                input_data={"user_input": user_input, "classification": classification.model_dump(), "safety": safety.model_dump()},
                output_data=medical_answer.model_dump(),
                metadata={"agent": "MedicalReasoningAgent", "duration_ms": duration_ms, "summary": f"Generated medical answer with {len(medical_answer.citations)} citations"},
                tool_name="medical_reasoning",
                duration_ms=duration_ms,
                success=True
            )
            
            trace["medical_reasoning"] = medical_answer.model_dump()
            
            # Update state
            old_state = current_state.copy()
            current_state.update({
                "medical_answer": medical_answer.model_dump(),
                "stage": "medical_reasoning_complete"
            })
            self.trace_manager.append_memory_update(
                session_id=session_id,
                old_state=old_state,
                new_state=current_state,
                cause="medical_reasoning_result",
                metadata={"agent": "MedicalReasoningAgent"}
            )

        except Exception as e:
            # Fail-safe: If Bedrock OR Valyu crashes
            progress("finalising", "pharmamiku is finalising answer")
            # Log error
            self.trace_manager.append_trace(
                session_id=session_id,
                step_type=StepType.TOOL_CALL,
                input_data={"user_input": user_input, "classification": classification.model_dump(), "safety": safety.model_dump()},
                output_data=None,
                metadata={"agent": "MedicalReasoningAgent", "summary": "Medical reasoning failed"},
                tool_name="medical_reasoning",
                duration_ms=0,
                success=False,
                error=str(e)
            )
            
            progress("finalising", "pharmamiku is finalising answer")
            fallback = (
                "⚠️ I had trouble generating a full medical explanation. "
                "Please consult a pharmacist or healthcare provider for accurate guidance."
            )
            trace["medical_reasoning_error"] = str(e)
            trace["final_answer"] = fallback
            
            # Update state
            old_state = current_state.copy()
            current_state.update({
                "error": str(e),
                "final_answer": fallback,
                "stage": "error"
            })
            self.trace_manager.append_memory_update(
                session_id=session_id,
                old_state=old_state,
                new_state=current_state,
                cause="medical_reasoning_error",
                metadata={"agent": "MedicalReasoningAgent"}
            )
            
            # Still run trace explainer
            try:
                start_time = time.time()
                trace_explanation = self.agent6.explain(
                    trace=trace,
                    user_message=user_input,
                    final_answer=fallback
                )
                duration_ms = (time.time() - start_time) * 1000
                
                self.trace_manager.append_trace(
                    session_id=session_id,
                    step_type=StepType.TOOL_CALL,
                    input_data={"trace": trace, "user_message": user_input, "final_answer": fallback},
                    output_data=trace_explanation.model_dump(),
                    metadata={"agent": "TraceExplainer", "duration_ms": duration_ms, "summary": "Generated trace explanation"},
                    tool_name="explain",
                    duration_ms=duration_ms,
                    success=True
                )
                
                trace["trace_explanation"] = trace_explanation.model_dump()
                
                # Append reasoning explanation
                reasoning_explanation = trace_explanation.trace_explanation_user_friendly
                if reasoning_explanation and reasoning_explanation.strip():
                    fallback = fallback + f"\n\n---\n\n💭 What happened:\n{reasoning_explanation}"
            except Exception as e2:
                trace["trace_explainer_error"] = str(e2)
                self.trace_manager.append_trace(
                    session_id=session_id,
                    step_type=StepType.TOOL_CALL,
                    input_data={"trace": trace, "user_message": user_input, "final_answer": fallback},
                    output_data=None,
                    metadata={"agent": "TraceExplainer", "summary": "Trace explainer failed"},
                    tool_name="explain",
                    duration_ms=0,
                    success=False,
                    error=str(e2)
                )
            
            # End trace
            structured_trace = self.trace_manager.end_trace(session_id)
            trace["structured_trace"] = structured_trace
            
            return fallback, trace

        # ------------------------------------------------------------
        # 4️⃣ PHARMA MIKU PERSONA LAYER
        # ------------------------------------------------------------
        try:
            progress("thinking", "pharmamiku is thinking")
            
            # Log decision: applying persona layer
            self.trace_manager.append_decision(
                session_id=session_id,
                input_state={"medical_answer": medical_answer.model_dump(), "safety": safety.model_dump(), "age_group": age_group},
                reasoning="Applying persona layer to make answer user-friendly",
                selected_action="apply_persona",
                metadata={"agent": "PharmaMikuAgent", "step": 4}
            )
            
            start_time = time.time()
            user_facing_answer = self.agent4.run(
                user_input=user_input,
                medical_answer=medical_answer,
                safety=safety,
                age_group=age_group if age_group != "unknown" else "adult"
            )
            duration_ms = (time.time() - start_time) * 1000
            
            # Log tool call result
            self.trace_manager.append_trace(
                session_id=session_id,
                step_type=StepType.TOOL_CALL,
                input_data={"medical_answer": medical_answer.model_dump(), "safety": safety.model_dump(), "age_group": age_group},
                output_data=user_facing_answer.model_dump(),
                metadata={"agent": "PharmaMikuAgent", "duration_ms": duration_ms, "summary": "Applied persona layer to answer"},
                tool_name="apply_persona",
                duration_ms=duration_ms,
                success=True
            )
            
            trace["pharma_miku"] = user_facing_answer.model_dump()
            
            # Update state
            old_state = current_state.copy()
            current_state.update({
                "user_facing_answer": user_facing_answer.model_dump(),
                "stage": "persona_applied"
            })
            self.trace_manager.append_memory_update(
                session_id=session_id,
                old_state=old_state,
                new_state=current_state,
                cause="persona_result",
                metadata={"agent": "PharmaMikuAgent"}
            )

        except Exception as e:
            progress("finalising", "pharmamiku is finalising answer")
            # Log error
            self.trace_manager.append_trace(
                session_id=session_id,
                step_type=StepType.TOOL_CALL,
                input_data={"medical_answer": medical_answer.model_dump(), "safety": safety.model_dump(), "age_group": age_group},
                output_data=None,
                metadata={"agent": "PharmaMikuAgent", "summary": "Persona layer failed"},
                tool_name="apply_persona",
                duration_ms=0,
                success=False,
                error=str(e)
            )
            
            progress("finalising", "pharmamiku is finalising answer")
            backup = (
                "Here is the medical information, but I could not apply the persona layer."
            )
            trace["pharma_miku_error"] = str(e)
            trace["final_answer"] = backup
            
            # Update state
            old_state = current_state.copy()
            current_state.update({
                "error": str(e),
                "final_answer": backup,
                "stage": "persona_error"
            })
            self.trace_manager.append_memory_update(
                session_id=session_id,
                old_state=old_state,
                new_state=current_state,
                cause="persona_error",
                metadata={"agent": "PharmaMikuAgent"}
            )
            
            # Still run trace explainer
            try:
                start_time = time.time()
                trace_explanation = self.agent6.explain(
                    trace=trace,
                    user_message=user_input,
                    final_answer=backup
                )
                duration_ms = (time.time() - start_time) * 1000
                
                self.trace_manager.append_trace(
                    session_id=session_id,
                    step_type=StepType.TOOL_CALL,
                    input_data={"trace": trace, "user_message": user_input, "final_answer": backup},
                    output_data=trace_explanation.model_dump(),
                    metadata={"agent": "TraceExplainer", "duration_ms": duration_ms, "summary": "Generated trace explanation"},
                    tool_name="explain",
                    duration_ms=duration_ms,
                    success=True
                )
                
                trace["trace_explanation"] = trace_explanation.model_dump()
                
                # Append reasoning explanation
                reasoning_explanation = trace_explanation.trace_explanation_user_friendly
                if reasoning_explanation and reasoning_explanation.strip():
                    backup = backup + f"\n\n---\n\n💭 What happened:\n{reasoning_explanation}"
            except Exception as e2:
                trace["trace_explainer_error"] = str(e2)
                self.trace_manager.append_trace(
                    session_id=session_id,
                    step_type=StepType.TOOL_CALL,
                    input_data={"trace": trace, "user_message": user_input, "final_answer": backup},
                    output_data=None,
                    metadata={"agent": "TraceExplainer", "summary": "Trace explainer failed"},
                    tool_name="explain",
                    duration_ms=0,
                    success=False,
                    error=str(e2)
                )
            
            # End trace
            structured_trace = self.trace_manager.end_trace(session_id)
            trace["structured_trace"] = structured_trace
            
            return backup, trace

        # ------------------------------------------------------------
        # 5️⃣ JUDGE AGENT (Final Safety & Quality Check)
        # ------------------------------------------------------------
        try:
            progress("judging", "pharmamiku is judging")
            
            # Log decision: starting judge evaluation
            self.trace_manager.append_decision(
                session_id=session_id,
                input_state={"user_facing_answer": user_facing_answer.model_dump(), "medical_answer": medical_answer.model_dump(), "risk_level": safety.risk_level},
                reasoning="Running final safety and quality check",
                selected_action="judge_evaluate",
                metadata={"agent": "JudgeAgent", "step": 5}
            )
            
            start_time = time.time()
            judge_verdict = self.agent5.evaluate(
                user_message=user_input,
                user_facing_answer=user_facing_answer,
                canonical_medical_answer=medical_answer,
                risk_level=safety.risk_level,
                safety_decision="ALLOW",  # We got past the early stop, so it's ALLOW
                needs_handoff=safety.needs_handoff
            )
            duration_ms = (time.time() - start_time) * 1000
            
            # Log tool call result
            self.trace_manager.append_trace(
                session_id=session_id,
                step_type=StepType.TOOL_CALL,
                input_data={"user_facing_answer": user_facing_answer.model_dump(), "medical_answer": medical_answer.model_dump()},
                output_data=judge_verdict.model_dump(),
                metadata={"agent": "JudgeAgent", "duration_ms": duration_ms, "summary": f"Judge verdict: {judge_verdict.verdict}"},
                tool_name="judge_evaluate",
                duration_ms=duration_ms,
                success=True
            )
            
            trace["judge"] = judge_verdict.model_dump()

            # Apply verdict (may adjust the answer)
            final_answer = self.agent5.apply_verdict(judge_verdict, user_facing_answer)
            trace["final_answer"] = final_answer.text
            trace["citations"] = final_answer.citations
            
            # Update state
            old_state = current_state.copy()
            current_state.update({
                "judge_verdict": judge_verdict.model_dump(),
                "final_answer": final_answer.text,
                "citations": final_answer.citations,
                "stage": "judged"
            })
            self.trace_manager.append_memory_update(
                session_id=session_id,
                old_state=old_state,
                new_state=current_state,
                cause="judge_result",
                metadata={"agent": "JudgeAgent"}
            )

        except Exception as e:
            # If judge fails, use the original answer
            print(f"❗ Judge Agent error: {e}")
            
            # Log error
            self.trace_manager.append_trace(
                session_id=session_id,
                step_type=StepType.TOOL_CALL,
                input_data={"user_facing_answer": user_facing_answer.model_dump(), "medical_answer": medical_answer.model_dump()},
                output_data=None,
                metadata={"agent": "JudgeAgent", "summary": "Judge evaluation failed"},
                tool_name="judge_evaluate",
                duration_ms=0,
                success=False,
                error=str(e)
            )
            
            trace["judge_error"] = str(e)
            final_answer = user_facing_answer
            trace["final_answer"] = final_answer.text
            trace["citations"] = final_answer.citations
            
            # Update state
            old_state = current_state.copy()
            current_state.update({
                "error": str(e),
                "final_answer": final_answer.text,
                "citations": final_answer.citations,
                "stage": "judge_error"
            })
            self.trace_manager.append_memory_update(
                session_id=session_id,
                old_state=old_state,
                new_state=current_state,
                cause="judge_error",
                metadata={"agent": "JudgeAgent"}
            )

        # ------------------------------------------------------------
        # 6️⃣ TRACE EXPLAINER (Glass Box Reasoning)
        # ------------------------------------------------------------
        try:
            progress("finalising", "pharmamiku is finalising answer")
            
            # Log decision: generating trace explanation
            self.trace_manager.append_decision(
                session_id=session_id,
                input_state={"trace": trace, "final_answer": final_answer.text},
                reasoning="Generating user-friendly trace explanation",
                selected_action="explain_trace",
                metadata={"agent": "TraceExplainer", "step": 6}
            )
            
            start_time = time.time()
            trace_explanation = self.agent6.explain(
                trace=trace,
                user_message=user_input,
                final_answer=final_answer.text
            )
            duration_ms = (time.time() - start_time) * 1000
            
            # Log tool call result
            self.trace_manager.append_trace(
                session_id=session_id,
                step_type=StepType.TOOL_CALL,
                input_data={"trace": trace, "user_message": user_input, "final_answer": final_answer.text},
                output_data=trace_explanation.model_dump(),
                metadata={"agent": "TraceExplainer", "duration_ms": duration_ms, "summary": "Generated trace explanation"},
                tool_name="explain",
                duration_ms=duration_ms,
                success=True
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
            
            # Log error
            self.trace_manager.append_trace(
                session_id=session_id,
                step_type=StepType.TOOL_CALL,
                input_data={"trace": trace, "user_message": user_input, "final_answer": final_answer.text},
                output_data=None,
                metadata={"agent": "TraceExplainer", "summary": "Trace explainer failed"},
                tool_name="explain",
                duration_ms=0,
                success=False,
                error=str(e)
            )
            
            trace["trace_explainer_error"] = str(e)
            final_answer_text = final_answer.text

        # End trace session
        structured_trace = self.trace_manager.end_trace(session_id)
        trace["structured_trace"] = structured_trace

        # Done! Return answer text (with reasoning) and trace (which includes citations)
        return final_answer_text, trace

