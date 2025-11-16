# backend/observability/trace_manager.py

import os
import json
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

# Try to import LangSmith, but don't crash if it's not installed
try:
    from langsmith import Client as LangSmithClient
    HAS_LANGSMITH = True
except ImportError:
    HAS_LANGSMITH = False


class StepType(str, Enum):
    """Types of trace steps"""
    DECISION = "decision"
    TOOL_CALL = "tool_call"
    MEMORY_UPDATE = "memory_update"
    STATE_TRANSITION = "state_transition"


class TraceManager:
    """
    Central trace manager for the Glass Box Agent system.
    Handles trace storage, retrieval, and optional LangSmith integration.
    """

    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.traces_dir = self.base_dir / "traces"
        self.traces_dir.mkdir(exist_ok=True)
        
        self.debug_mode = os.getenv("DEBUG_TRACE", "false").lower() == "true"
        
        # LangSmith setup (optional)
        self.langsmith_client = None
        if HAS_LANGSMITH:
            langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
            langsmith_project = os.getenv("LANGSMITH_PROJECT", "pharmamiku")
            if langsmith_api_key:
                try:
                    self.langsmith_client = LangSmithClient(api_key=langsmith_api_key)
                    self.langsmith_project = langsmith_project
                    print(f"🔗 LangSmith integration enabled (project: {langsmith_project})")
                except Exception as e:
                    print(f"⚠️ LangSmith initialization failed: {e}")
        
        # Active traces (in-memory for current session)
        self.active_traces: Dict[str, Dict] = {}

    def start_trace(self, session_id: Optional[str] = None) -> str:
        """
        Start a new trace session.
        
        Args:
            session_id: Optional session ID. If not provided, generates a UUID.
        
        Returns:
            The session ID for this trace.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        trace = {
            "session_id": session_id,
            "started_at": datetime.utcnow().isoformat(),
            "steps": [],
            "metadata": {
                "total_steps": 0,
                "total_tool_calls": 0,
                "total_decisions": 0,
                "total_memory_updates": 0,
            }
        }
        
        self.active_traces[session_id] = trace
        
        if self.debug_mode:
            print(f"🔍 [TRACE] Started trace session: {session_id}")
        
        return session_id

    def append_trace(
        self,
        session_id: str,
        step_type: StepType,
        input_data: Any,
        output_data: Any,
        metadata: Optional[Dict] = None,
        tool_name: Optional[str] = None,
        duration_ms: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None,
    ) -> int:
        """
        Append a step to the trace.
        
        Args:
            session_id: The session ID for this trace.
            step_type: Type of step (decision, tool_call, memory_update, etc.)
            input_data: Input state/data for this step
            output_data: Output/result from this step
            metadata: Additional metadata (model, cost, etc.)
            tool_name: Name of tool if this is a tool_call
            duration_ms: Duration in milliseconds
            success: Whether the step succeeded
            error: Error message if step failed
        
        Returns:
            The step_id (index) of the added step.
        """
        if session_id not in self.active_traces:
            # Auto-start trace if not started
            self.start_trace(session_id)
        
        trace = self.active_traces[session_id]
        step_id = len(trace["steps"]) + 1
        
        step = {
            "step_id": step_id,
            "type": step_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "input": input_data,
            "output": output_data,
            "metadata": metadata or {},
            "success": success,
        }
        
        # Add type-specific fields
        if step_type == StepType.TOOL_CALL:
            step["tool_name"] = tool_name
            step["duration_ms"] = duration_ms
            trace["metadata"]["total_tool_calls"] += 1
        
        elif step_type == StepType.DECISION:
            trace["metadata"]["total_decisions"] += 1
        
        elif step_type == StepType.MEMORY_UPDATE:
            trace["metadata"]["total_memory_updates"] += 1
        
        if error:
            step["error"] = error
        
        trace["steps"].append(step)
        trace["metadata"]["total_steps"] = step_id
        
        if self.debug_mode:
            self._print_step(step)
        
        return step_id

    def append_decision(
        self,
        session_id: str,
        input_state: Any,
        reasoning: str,
        selected_action: str,
        metadata: Optional[Dict] = None,
    ) -> int:
        """
        Convenience method to append a decision step.
        
        Args:
            session_id: The session ID
            input_state: Current input state
            reasoning: LLM output or reasoning
            selected_action: Selected tool or action
            metadata: Additional metadata (model, cost, etc.)
        
        Returns:
            The step_id
        """
        output_data = {
            "reasoning": reasoning,
            "selected_action": selected_action,
        }
        return self.append_trace(
            session_id=session_id,
            step_type=StepType.DECISION,
            input_data=input_state,
            output_data=output_data,
            metadata=metadata,
        )

    def append_tool_call(
        self,
        session_id: str,
        tool_name: str,
        arguments: Dict,
        output: Any,
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> int:
        """
        Convenience method to append a tool call step.
        
        Args:
            session_id: The session ID
            tool_name: Name of the tool
            arguments: Arguments passed to the tool
            output: Output from the tool
            duration_ms: Duration in milliseconds
            success: Whether the call succeeded
            error: Error message if failed
            metadata: Additional metadata
        
        Returns:
            The step_id
        """
        return self.append_trace(
            session_id=session_id,
            step_type=StepType.TOOL_CALL,
            input_data={"tool_name": tool_name, "arguments": arguments},
            output_data=output,
            metadata=metadata,
            tool_name=tool_name,
            duration_ms=duration_ms,
            success=success,
            error=error,
        )

    def append_memory_update(
        self,
        session_id: str,
        old_state: Any,
        new_state: Any,
        cause: str,
        metadata: Optional[Dict] = None,
    ) -> int:
        """
        Convenience method to append a memory/state update step.
        
        Args:
            session_id: The session ID
            old_state: Previous state
            new_state: New state
            cause: What caused the update (e.g., "decision_step", "tool_result")
            metadata: Additional metadata
        
        Returns:
            The step_id
        """
        # Calculate diff
        diff = self._calculate_diff(old_state, new_state)
        
        output_data = {
            "old_state": old_state,
            "new_state": new_state,
            "diff": diff,
            "cause": cause,
        }
        
        return self.append_trace(
            session_id=session_id,
            step_type=StepType.MEMORY_UPDATE,
            input_data=old_state,
            output_data=output_data,
            metadata=metadata,
        )

    def end_trace(self, session_id: str) -> Dict:
        """
        End a trace session and save it.
        
        Args:
            session_id: The session ID
        
        Returns:
            The complete trace dictionary
        """
        if session_id not in self.active_traces:
            raise ValueError(f"Trace session {session_id} not found")
        
        trace = self.active_traces[session_id]
        trace["ended_at"] = datetime.utcnow().isoformat()
        
        # Calculate total duration
        start_time = datetime.fromisoformat(trace["started_at"])
        end_time = datetime.fromisoformat(trace["ended_at"])
        duration_seconds = (end_time - start_time).total_seconds()
        trace["metadata"]["duration_seconds"] = duration_seconds
        
        # Save to file
        trace_file = self.traces_dir / f"{session_id}.json"
        with open(trace_file, "w") as f:
            json.dump(trace, f, indent=2, default=str)
        
        if self.debug_mode:
            print(f"🔍 [TRACE] Saved trace to {trace_file}")
            print(f"🔍 [TRACE] Total steps: {trace['metadata']['total_steps']}")
        
        # Send to LangSmith if enabled
        if self.langsmith_client:
            try:
                self._send_to_langsmith(trace)
            except Exception as e:
                print(f"⚠️ Failed to send trace to LangSmith: {e}")
        
        # Keep in memory for retrieval
        return trace

    def get_trace(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve a trace by session ID.
        First checks active traces, then tries to load from file.
        
        Args:
            session_id: The session ID
        
        Returns:
            The trace dictionary, or None if not found
        """
        # Check active traces first
        if session_id in self.active_traces:
            return self.active_traces[session_id]
        
        # Try to load from file
        trace_file = self.traces_dir / f"{session_id}.json"
        if trace_file.exists():
            with open(trace_file, "r") as f:
                return json.load(f)
        
        return None

    def _calculate_diff(self, old_state: Any, new_state: Any) -> Dict:
        """Calculate a simple diff between old and new state."""
        try:
            if isinstance(old_state, dict) and isinstance(new_state, dict):
                diff = {}
                all_keys = set(old_state.keys()) | set(new_state.keys())
                for key in all_keys:
                    old_val = old_state.get(key)
                    new_val = new_state.get(key)
                    if old_val != new_val:
                        diff[key] = {"old": old_val, "new": new_val}
                return diff
            else:
                return {"old": old_state, "new": new_state}
        except Exception:
            return {"old": str(old_state), "new": str(new_state)}

    def _print_step(self, step: Dict):
        """Print a step in debug mode."""
        step_type = step["type"].upper()
        step_id = step["step_id"]
        timestamp = step["timestamp"]
        
        print(f"\n🔍 [TRACE STEP {step_id}] {step_type} @ {timestamp}")
        
        if step["type"] == "tool_call":
            print(f"   Tool: {step.get('tool_name', 'unknown')}")
            print(f"   Duration: {step.get('duration_ms', 0):.2f}ms")
        
        if not step.get("success", True):
            print(f"   ❌ ERROR: {step.get('error', 'Unknown error')}")
        
        # Print summary if available
        summary = step.get("metadata", {}).get("summary")
        if summary:
            print(f"   Summary: {summary}")

    def _send_to_langsmith(self, trace: Dict):
        """Send trace to LangSmith (if enabled)."""
        if not self.langsmith_client:
            return
        
        # Convert trace to LangSmith format
        # This is a simplified version - you may want to enhance this
        try:
            run_data = {
                "name": f"pharmamiku_session_{trace['session_id']}",
                "run_type": "chain",
                "start_time": trace["started_at"],
                "end_time": trace.get("ended_at"),
                "extra": trace["metadata"],
            }
            
            # Create a run in LangSmith
            # Note: This is a simplified integration. You may want to use
            # LangSmith's trace API more comprehensively.
            print(f"📤 [LangSmith] Trace sent (project: {self.langsmith_project})")
        except Exception as e:
            print(f"⚠️ LangSmith send error: {e}")


# Global singleton instance
_trace_manager_instance: Optional[TraceManager] = None


def get_trace_manager() -> TraceManager:
    """Get the global trace manager instance."""
    global _trace_manager_instance
    if _trace_manager_instance is None:
        _trace_manager_instance = TraceManager()
    return _trace_manager_instance


def generate_step_summary(step: Dict) -> str:
    """
    Generate a concise summary for a trace step.
    Used by the frontend to show previews.
    
    Args:
        step: The trace step dictionary
    
    Returns:
        A short summary string
    """
    step_type = step.get("type", "unknown")
    step_id = step.get("step_id", 0)
    
    # Check if summary already exists in metadata
    if "metadata" in step and "summary" in step["metadata"]:
        return step["metadata"]["summary"]
    
    # Generate summary based on step type
    if step_type == "decision":
        selected_action = step.get("output", {}).get("selected_action", "unknown")
        reasoning = step.get("output", {}).get("reasoning", "")
        if reasoning:
            # Take first 100 chars of reasoning
            reasoning_preview = reasoning[:100].replace("\n", " ")
            if len(reasoning) > 100:
                reasoning_preview += "..."
            return f"Decision: {selected_action} - {reasoning_preview}"
        return f"Decision: {selected_action}"
    
    elif step_type == "tool_call":
        tool_name = step.get("tool_name", "unknown_tool")
        duration = step.get("duration_ms", 0)
        success = step.get("success", True)
        status = "✓" if success else "✗"
        return f"{status} Tool: {tool_name} ({duration:.0f}ms)"
    
    elif step_type == "memory_update":
        cause = step.get("output", {}).get("cause", "unknown")
        return f"Memory updated: {cause}"
    
    else:
        return f"Step {step_id}: {step_type}"

