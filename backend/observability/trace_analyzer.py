# backend/observability/trace_analyzer.py

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from datetime import datetime
import statistics


class TraceAnalyzer:
    """
    Analyzes agent execution traces to extract behavioral insights,
    patterns, and metrics for the Glass Box Agent system.
    """

    def __init__(self, traces_dir: Optional[Path] = None):
        """
        Initialize the trace analyzer.
        
        Args:
            traces_dir: Directory containing trace JSON files. 
                       Defaults to backend/traces/
        """
        if traces_dir is None:
            base_dir = Path(__file__).resolve().parent.parent
            traces_dir = base_dir / "traces"
        
        self.traces_dir = Path(traces_dir)
        self.traces_dir.mkdir(exist_ok=True)

    def load_all_traces(self) -> List[Dict]:
        """
        Load all trace files from the traces directory.
        
        Returns:
            List of trace dictionaries
        """
        traces = []
        
        if not self.traces_dir.exists():
            return traces
        
        for trace_file in self.traces_dir.glob("*.json"):
            try:
                with open(trace_file, "r") as f:
                    trace = json.load(f)
                    trace["_file"] = str(trace_file.name)  # Store filename for reference
                    traces.append(trace)
            except Exception as e:
                print(f"⚠️ Error loading trace {trace_file}: {e}")
        
        return traces

    def extract_tool_metrics(self, trace: Dict) -> Dict[str, Any]:
        """
        Extract tool usage metrics from a single trace.
        
        Returns:
            Dictionary with tool metrics
        """
        tool_calls = []
        tool_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_duration_ms": 0,
            "tool_usage": defaultdict(int),
            "tool_success": defaultdict(int),
            "tool_failures": defaultdict(int),
            "tool_durations": defaultdict(list),
        }

        for step in trace.get("steps", []):
            if step.get("type") == "tool_call":
                tool_stats["total_calls"] += 1
                tool_name = step.get("tool_name", "unknown")
                success = step.get("success", True)
                duration = step.get("duration_ms", 0)

                tool_stats["tool_usage"][tool_name] += 1
                tool_stats["tool_durations"][tool_name].append(duration)
                tool_stats["total_duration_ms"] += duration

                if success:
                    tool_stats["successful_calls"] += 1
                    tool_stats["tool_success"][tool_name] += 1
                else:
                    tool_stats["failed_calls"] += 1
                    tool_stats["tool_failures"][tool_name] += 1
                    tool_calls.append({
                        "tool": tool_name,
                        "error": step.get("error", "Unknown error"),
                        "step_id": step.get("step_id"),
                    })

        return {
            **tool_stats,
            "failed_tool_calls": tool_calls,
        }

    def detect_shortcut(self, trace: Dict) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect if a trace contains shortcuts (factual claims without supporting tool calls).
        
        A shortcut is suspected if:
        - Final answer contains factual claims
        - No tool calls returned data that could support those claims
        - Or tool calls failed but answer still contains specific information
        
        Returns:
            Tuple of (is_shortcut, details_dict)
        """
        steps = trace.get("steps", [])
        final_answer = trace.get("final_answer", "")
        
        # Get all tool calls
        tool_calls = [s for s in steps if s.get("type") == "tool_call"]
        successful_tools = [s for s in tool_calls if s.get("success", True)]
        failed_tools = [s for s in tool_calls if not s.get("success", True)]
        
        # Check if we have a final answer
        if not final_answer or len(final_answer.strip()) < 10:
            return False, {"reason": "No final answer"}
        
        # Check for evidence of tool usage that should support the answer
        # Look for medical reasoning, evidence retrieval, or research tools
        evidence_tools = ["valyu_search", "medical_reasoning", "fetch_evidence"]
        has_evidence_tool = any(
            tool.get("tool_name") in evidence_tools 
            for tool in successful_tools
        )
        
        # Check if answer contains specific factual claims (numbers, medical terms, etc.)
        # Simple heuristic: if answer is substantial and contains medical terms
        medical_indicators = [
            "mg", "dose", "medication", "drug", "side effect", 
            "interaction", "contraindication", "dosage"
        ]
        has_medical_content = any(
            indicator.lower() in final_answer.lower() 
            for indicator in medical_indicators
        )
        
        # Shortcut suspected if:
        # 1. Answer has medical content
        # 2. But no evidence tools were successfully called
        # 3. OR evidence tools failed but answer still has specific content
        is_shortcut = False
        reason = ""
        
        if has_medical_content:
            if not has_evidence_tool:
                is_shortcut = True
                reason = "Medical content in answer but no evidence retrieval tools used"
            elif len(failed_tools) > 0 and len(successful_tools) == 0:
                is_shortcut = True
                reason = "All evidence tools failed but answer contains medical content"
        
        return is_shortcut, {
            "reason": reason,
            "has_medical_content": has_medical_content,
            "has_evidence_tool": has_evidence_tool,
            "successful_tool_count": len(successful_tools),
            "failed_tool_count": len(failed_tools),
            "answer_length": len(final_answer),
        }

    def extract_step_metrics(self, trace: Dict) -> Dict[str, Any]:
        """
        Extract metrics about step types and distribution.
        
        Returns:
            Dictionary with step metrics
        """
        steps = trace.get("steps", [])
        step_types = Counter(s.get("type", "unknown") for s in steps)
        
        step_durations = defaultdict(list)
        step_latencies = []
        
        for step in steps:
            step_type = step.get("type", "unknown")
            duration = step.get("duration_ms", 0)
            if duration > 0:
                step_durations[step_type].append(duration)
                step_latencies.append(duration)
        
        # Calculate average latencies per step type
        avg_latencies = {
            step_type: statistics.mean(durations) if durations else 0
            for step_type, durations in step_durations.items()
        }
        
        return {
            "total_steps": len(steps),
            "step_type_distribution": dict(step_types),
            "step_type_latencies": {
                step_type: {
                    "avg_ms": statistics.mean(durations) if durations else 0,
                    "min_ms": min(durations) if durations else 0,
                    "max_ms": max(durations) if durations else 0,
                    "count": len(durations),
                }
                for step_type, durations in step_durations.items()
            },
            "overall_avg_latency_ms": statistics.mean(step_latencies) if step_latencies else 0,
        }

    def extract_error_patterns(self, trace: Dict) -> List[Dict[str, Any]]:
        """
        Extract error patterns from a trace.
        
        Returns:
            List of error details
        """
        errors = []
        
        for step in trace.get("steps", []):
            if not step.get("success", True):
                error_info = {
                    "step_id": step.get("step_id"),
                    "step_type": step.get("type"),
                    "tool_name": step.get("tool_name"),
                    "error": step.get("error", "Unknown error"),
                    "timestamp": step.get("timestamp"),
                }
                errors.append(error_info)
        
        return errors

    def analyze_failures(self, trace: Dict) -> Dict[str, Any]:
        """
        Perform root cause analysis of failures in a trace.
        
        Returns:
            Dictionary with failure analysis including root causes and recommendations
        """
        failures = []
        steps = trace.get("steps", [])
        
        for step in steps:
            if not step.get("success", True):
                step_id = step.get("step_id")
                step_type = step.get("type", "unknown")
                error = step.get("error", "Unknown error")
                tool_name = step.get("tool_name")
                timestamp = step.get("timestamp")
                
                # Determine root cause
                root_cause = "unknown"
                derived_from_step_id = None
                
                if step_type == "tool_call" and tool_name:
                    root_cause = f"tool:{tool_name}"
                elif step_type == "decision":
                    root_cause = "llm"
                    # Check if this decision step failed due to a previous tool failure
                    # Look at previous steps to find potential upstream failures
                    for prev_step in steps:
                        if prev_step.get("step_id", 0) < step_id and not prev_step.get("success", True):
                            if prev_step.get("type") == "tool_call":
                                derived_from_step_id = prev_step.get("step_id")
                                root_cause = f"tool:{prev_step.get('tool_name', 'unknown')}"
                                break
                elif step_type == "memory_update":
                    root_cause = "memory"
                else:
                    # Check if error mentions user input
                    error_lower = error.lower()
                    if any(keyword in error_lower for keyword in ["user", "input", "request", "invalid"]):
                        root_cause = "user_input"
                
                # Determine severity (simple heuristic)
                severity = "medium"
                if "critical" in error.lower() or "fatal" in error.lower():
                    severity = "high"
                elif "warning" in error.lower() or "timeout" in error.lower():
                    severity = "low"
                
                failure = {
                    "step_id": step_id,
                    "step_type": step_type,
                    "tool_name": tool_name,
                    "error": error,
                    "timestamp": timestamp,
                    "root_cause": root_cause,
                    "derived_from_step_id": derived_from_step_id,
                    "severity": severity,
                }
                
                # Generate recommendation
                recommendation = self._generate_failure_recommendation(failure, step)
                failure["recommendation"] = recommendation
                failure["confidence"] = 0.8  # Default confidence
                
                failures.append(failure)
        
        return {
            "session_id": trace.get("session_id"),
            "total_failures": len(failures),
            "failures": failures,
        }

    def _generate_failure_recommendation(self, failure: Dict, step: Dict) -> str:
        """
        Generate actionable recommendation for a specific failure.
        
        Args:
            failure: Failure dictionary
            step: Original step dictionary
        
        Returns:
            Recommendation string
        """
        root_cause = failure.get("root_cause", "")
        error = failure.get("error", "").lower()
        
        if root_cause.startswith("tool:"):
            tool_name = root_cause.split(":")[1]
            if "timeout" in error or "connection" in error:
                return f"Retry tool call to {tool_name} with exponential backoff. Consider increasing timeout."
            elif "rate limit" in error or "quota" in error:
                return f"Implement rate limiting for {tool_name}. Add queue or delay between calls."
            elif "authentication" in error or "permission" in error:
                return f"Check API credentials for {tool_name}. Verify permissions and access tokens."
            else:
                return f"Add retry logic with fallback for {tool_name}. Handle exceptions gracefully."
        
        elif root_cause == "llm":
            if "timeout" in error:
                return "Increase LLM timeout or reduce prompt size. Consider streaming responses."
            elif "rate limit" in error:
                return "Implement rate limiting for LLM calls. Add queue or request throttling."
            elif "invalid" in error or "format" in error:
                return "Adjust prompt format or structure. Validate input before sending to LLM."
            else:
                return "Retry LLM call with adjusted parameters. Consider increasing temperature or verbosity."
        
        elif root_cause == "memory":
            return "Validate memory updates before applying. Add consistency checks and rollback mechanism."
        
        elif root_cause == "user_input":
            return "Add input validation and sanitization. Provide clear error messages to user."
        
        else:
            return "Review error handling for this step type. Add logging and monitoring."

    def analyze_all_traces(self) -> Dict[str, Any]:
        """
        Analyze all traces and generate comprehensive insights.
        
        Returns:
            Dictionary containing all analysis results
        """
        traces = self.load_all_traces()
        
        if not traces:
            return {
                "summary": "No traces found",
                "total_traces": 0,
                "generated_at": datetime.utcnow().isoformat(),
            }
        
        # Aggregate metrics
        all_tool_metrics = []
        all_step_metrics = []
        all_errors = []
        shortcut_traces = []
        
        # Per-trace analysis
        for trace in traces:
            # Tool metrics
            tool_metrics = self.extract_tool_metrics(trace)
            tool_metrics["session_id"] = trace.get("session_id")
            all_tool_metrics.append(tool_metrics)
            
            # Step metrics
            step_metrics = self.extract_step_metrics(trace)
            step_metrics["session_id"] = trace.get("session_id")
            all_step_metrics.append(step_metrics)
            
            # Error patterns
            errors = self.extract_error_patterns(trace)
            for error in errors:
                error["session_id"] = trace.get("session_id")
            all_errors.extend(errors)
            
            # Shortcut detection
            is_shortcut, shortcut_details = self.detect_shortcut(trace)
            if is_shortcut:
                shortcut_traces.append({
                    "session_id": trace.get("session_id"),
                    "details": shortcut_details,
                })
        
        # Failure analysis
        all_failure_analyses = []
        for trace in traces:
            failure_analysis = self.analyze_failures(trace)
            if failure_analysis["total_failures"] > 0:
                all_failure_analyses.append(failure_analysis)
        
        # Aggregate failure statistics
        failure_by_root_cause = Counter()
        failure_by_tool = Counter()
        failure_by_step_type = Counter()
        recurring_failures = Counter()
        
        for analysis in all_failure_analyses:
            for failure in analysis["failures"]:
                failure_by_root_cause[failure["root_cause"]] += 1
                failure_by_step_type[failure["step_type"]] += 1
                if failure.get("tool_name"):
                    failure_by_tool[failure["tool_name"]] += 1
                # Track recurring errors
                error_key = f"{failure['root_cause']}:{failure['error'][:50]}"
                recurring_failures[error_key] += 1
        
        # Aggregate statistics
        total_tool_calls = sum(m["total_calls"] for m in all_tool_metrics)
        total_successful = sum(m["successful_calls"] for m in all_tool_metrics)
        total_failed = sum(m["failed_calls"] for m in all_tool_metrics)
        
        # Tool usage aggregation
        tool_usage_total = Counter()
        tool_success_total = Counter()
        tool_failures_total = Counter()
        tool_durations_agg = defaultdict(list)
        
        for metrics in all_tool_metrics:
            tool_usage_total.update(metrics["tool_usage"])
            tool_success_total.update(metrics["tool_success"])
            tool_failures_total.update(metrics["tool_failures"])
            
            for tool, durations in metrics["tool_durations"].items():
                tool_durations_agg[tool].extend(durations)
        
        # Calculate tool success rates
        tool_success_rates = {}
        for tool in tool_usage_total:
            success_count = tool_success_total.get(tool, 0)
            total_count = tool_usage_total.get(tool, 0)
            tool_success_rates[tool] = {
                "success_rate": success_count / total_count if total_count > 0 else 0,
                "total_calls": total_count,
                "successful": success_count,
                "failed": tool_failures_total.get(tool, 0),
                "avg_duration_ms": statistics.mean(tool_durations_agg[tool]) if tool_durations_agg[tool] else 0,
                "min_duration_ms": min(tool_durations_agg[tool]) if tool_durations_agg[tool] else 0,
                "max_duration_ms": max(tool_durations_agg[tool]) if tool_durations_agg[tool] else 0,
            }
        
        # Step type aggregation
        step_type_counts = Counter()
        step_type_latencies_agg = defaultdict(list)
        
        for metrics in all_step_metrics:
            step_type_counts.update(metrics["step_type_distribution"])
            for step_type, latencies in metrics["step_type_latencies"].items():
                step_type_latencies_agg[step_type].extend(
                    [latencies["avg_ms"]] * latencies["count"]
                )
        
        # Error pattern analysis
        error_types = Counter(e["error"] for e in all_errors)
        error_by_tool = Counter(e["tool_name"] for e in all_errors if e.get("tool_name"))
        error_by_step_type = Counter(e["step_type"] for e in all_errors)
        
        # Build insights
        insights = {
            "summary": {
                "total_traces": len(traces),
                "total_tool_calls": total_tool_calls,
                "total_successful_calls": total_successful,
                "total_failed_calls": total_failed,
                "overall_success_rate": total_successful / total_tool_calls if total_tool_calls > 0 else 0,
                "shortcut_rate": len(shortcut_traces) / len(traces) if traces else 0,
                "total_errors": len(all_errors),
                "generated_at": datetime.utcnow().isoformat(),
            },
            "tool_metrics": {
                "most_used_tools": dict(tool_usage_total.most_common(10)),
                "tool_success_rates": tool_success_rates,
                "tool_reliability_ranking": sorted(
                    tool_success_rates.items(),
                    key=lambda x: x[1]["success_rate"],
                    reverse=True
                )[:10],
            },
            "step_metrics": {
                "step_type_distribution": dict(step_type_counts),
                "step_type_avg_latencies": {
                    step_type: {
                        "avg_ms": statistics.mean(latencies) if latencies else 0,
                        "min_ms": min(latencies) if latencies else 0,
                        "max_ms": max(latencies) if latencies else 0,
                        "count": len(latencies),
                    }
                    for step_type, latencies in step_type_latencies_agg.items()
                },
            },
            "shortcuts": {
                "total_suspected": len(shortcut_traces),
                "shortcut_rate": len(shortcut_traces) / len(traces) if traces else 0,
                "traces_with_shortcuts": shortcut_traces[:20],  # Limit to top 20
            },
            "error_patterns": {
                "most_common_errors": dict(error_types.most_common(10)),
                "errors_by_tool": dict(error_by_tool.most_common(10)),
                "errors_by_step_type": dict(error_by_step_type),
                "total_error_count": len(all_errors),
            },
            "bottlenecks": self._identify_bottlenecks(
                tool_success_rates, step_type_latencies_agg, error_by_tool
            ),
            "recommendations": self._generate_recommendations(
                tool_success_rates, shortcut_traces, error_by_tool, error_types
            ),
            "failure_analysis": {
                "total_traces_with_failures": len(all_failure_analyses),
                "total_failures": sum(a.get("total_failures", 0) for a in all_failure_analyses),
                "failure_rate": len(all_failure_analyses) / len(traces) if traces else 0,
                "failures_by_root_cause": dict(failure_by_root_cause.most_common(10)),
                "failures_by_tool": dict(failure_by_tool.most_common(10)),
                "failures_by_step_type": dict(failure_by_step_type),
                "recurring_failures": [
                    {
                        "pattern": pattern,
                        "count": count,
                        "root_cause": pattern.split(":")[0] if ":" in pattern else "unknown",
                    }
                    for pattern, count in recurring_failures.most_common(10)
                ],
                "failure_reports": all_failure_analyses[:20] if all_failure_analyses else [],  # Limit to top 20
            },
        }
        
        return insights

    def _identify_bottlenecks(
        self,
        tool_success_rates: Dict,
        step_type_latencies: Dict,
        error_by_tool: Counter,
    ) -> Dict[str, Any]:
        """
        Identify bottlenecks and risk points in the system.
        
        Returns:
            Dictionary with bottleneck analysis
        """
        bottlenecks = {
            "slow_steps": [],
            "unreliable_tools": [],
            "high_error_tools": [],
        }
        
        # Find slow steps (above average latency)
        all_latencies = []
        for latencies in step_type_latencies.values():
            all_latencies.extend(latencies)
        
        avg_latency = statistics.mean(all_latencies) if all_latencies else 0
        
        for step_type, latencies in step_type_latencies.items():
            if latencies:
                avg = statistics.mean(latencies)
                if avg > avg_latency * 1.5:  # 50% above average
                    bottlenecks["slow_steps"].append({
                        "step_type": step_type,
                        "avg_latency_ms": avg,
                        "count": len(latencies),
                    })
        
        # Find unreliable tools (low success rate)
        for tool, metrics in tool_success_rates.items():
            if metrics["total_calls"] >= 3:  # Only consider tools used multiple times
                if metrics["success_rate"] < 0.8:  # Less than 80% success
                    bottlenecks["unreliable_tools"].append({
                        "tool": tool,
                        "success_rate": metrics["success_rate"],
                        "total_calls": metrics["total_calls"],
                    })
        
        # Find high error tools
        for tool, error_count in error_by_tool.most_common(5):
            bottlenecks["high_error_tools"].append({
                "tool": tool,
                "error_count": error_count,
            })
        
        return bottlenecks

    def _generate_recommendations(
        self,
        tool_success_rates: Dict,
        shortcut_traces: List,
        error_by_tool: Counter,
        error_types: Counter,
    ) -> List[str]:
        """
        Generate actionable recommendations based on analysis.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Tool reliability recommendations
        unreliable_tools = [
            tool for tool, metrics in tool_success_rates.items()
            if metrics["total_calls"] >= 3 and metrics["success_rate"] < 0.8
        ]
        
        if unreliable_tools:
            recommendations.append(
                f"Consider adding retry logic or fallback mechanisms for: {', '.join(unreliable_tools)}"
            )
        
        # Shortcut recommendations
        if len(shortcut_traces) > 0:
            shortcut_rate = len(shortcut_traces) / max(1, len(shortcut_traces))
            if shortcut_rate > 0.1:  # More than 10% shortcuts
                recommendations.append(
                    f"High shortcut rate detected ({shortcut_rate:.1%}). "
                    "Consider adding verification steps to ensure answers are backed by evidence."
                )
        
        # Error pattern recommendations
        if error_types:
            most_common_error = error_types.most_common(1)[0]
            if most_common_error[1] >= 3:
                recommendations.append(
                    f"Recurring error detected: '{most_common_error[0]}' "
                    f"(occurred {most_common_error[1]} times). "
                    "Consider adding error handling or validation."
                )
        
        # High error tool recommendations
        if error_by_tool:
            top_error_tool = error_by_tool.most_common(1)[0]
            if top_error_tool[1] >= 3:
                recommendations.append(
                    f"Tool '{top_error_tool[0]}' has {top_error_tool[1]} errors. "
                    "Review error handling and consider adding retries or fallbacks."
                )
        
        if not recommendations:
            recommendations.append("System appears to be performing well. No critical issues detected.")
        
        return recommendations

    def generate_report(self, insights: Dict[str, Any]) -> str:
        """
        Generate a human-readable report from insights.
        
        Returns:
            Plain English report string
        """
        summary = insights["summary"]
        tool_metrics = insights["tool_metrics"]
        shortcuts = insights["shortcuts"]
        error_patterns = insights["error_patterns"]
        bottlenecks = insights["bottlenecks"]
        recommendations = insights["recommendations"]
        
        report = []
        report.append("=" * 80)
        report.append("GLASS BOX AGENT - BEHAVIORAL INSIGHTS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {summary['generated_at']}")
        report.append("")
        
        # Summary
        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Total Traces Analyzed: {summary['total_traces']}")
        report.append(f"Total Tool Calls: {summary['total_tool_calls']}")
        report.append(f"Overall Success Rate: {summary['overall_success_rate']:.1%}")
        report.append(f"Shortcut Rate: {shortcuts['shortcut_rate']:.1%}")
        report.append(f"Total Errors: {summary['total_errors']}")
        report.append("")
        
        # Tool Reliability
        report.append("TOOL RELIABILITY")
        report.append("-" * 80)
        if tool_metrics["tool_reliability_ranking"]:
            report.append("Most Reliable Tools (by success rate):")
            for tool, metrics in tool_metrics["tool_reliability_ranking"][:5]:
                report.append(
                    f"  • {tool}: {metrics['success_rate']:.1%} "
                    f"({metrics['successful']}/{metrics['total_calls']} calls, "
                    f"avg {metrics['avg_duration_ms']:.0f}ms)"
                )
        report.append("")
        
        # Most Used Tools
        report.append("MOST USED TOOLS")
        report.append("-" * 80)
        for tool, count in list(tool_metrics["most_used_tools"].items())[:5]:
            report.append(f"  • {tool}: {count} calls")
        report.append("")
        
        # Shortcuts
        report.append("SHORTCUT DETECTION")
        report.append("-" * 80)
        report.append(f"Suspected Shortcuts: {shortcuts['total_suspected']} traces")
        report.append(f"Shortcut Rate: {shortcuts['shortcut_rate']:.1%}")
        if shortcuts["traces_with_shortcuts"]:
            report.append("Sample traces with suspected shortcuts:")
            for trace in shortcuts["traces_with_shortcuts"][:3]:
                report.append(f"  • Session {trace['session_id'][:8]}...: {trace['details']['reason']}")
        report.append("")
        
        # Error Patterns
        report.append("ERROR PATTERNS")
        report.append("-" * 80)
        if error_patterns["most_common_errors"]:
            report.append("Most Common Errors:")
            for error, count in list(error_patterns["most_common_errors"].items())[:5]:
                report.append(f"  • {error}: {count} occurrences")
        report.append("")
        
        # Bottlenecks
        report.append("BOTTLENECKS & RISK POINTS")
        report.append("-" * 80)
        if bottlenecks["slow_steps"]:
            report.append("Slow Steps (above average latency):")
            for step in bottlenecks["slow_steps"]:
                report.append(
                    f"  • {step['step_type']}: {step['avg_latency_ms']:.0f}ms "
                    f"({step['count']} occurrences)"
                )
        
        if bottlenecks["unreliable_tools"]:
            report.append("Unreliable Tools (low success rate):")
            for tool in bottlenecks["unreliable_tools"]:
                report.append(
                    f"  • {tool['tool']}: {tool['success_rate']:.1%} "
                    f"({tool['total_calls']} calls)"
                )
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 80)
        for i, rec in enumerate(recommendations, 1):
            report.append(f"{i}. {rec}")
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

    def export_to_csv(self, insights: Dict[str, Any], output_path: Path) -> None:
        """
        Export insights to CSV format for dashboard integration.
        
        Args:
            insights: Insights dictionary
            output_path: Path to save CSV file
        """
        import csv
        
        # Tool metrics CSV
        tool_csv_path = output_path.parent / f"{output_path.stem}_tools.csv"
        with open(tool_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Tool", "Total Calls", "Successful", "Failed", 
                "Success Rate", "Avg Duration (ms)", "Min Duration (ms)", "Max Duration (ms)"
            ])
            
            for tool, metrics in insights["tool_metrics"]["tool_success_rates"].items():
                writer.writerow([
                    tool,
                    metrics["total_calls"],
                    metrics["successful"],
                    metrics["failed"],
                    f"{metrics['success_rate']:.2%}",
                    f"{metrics['avg_duration_ms']:.2f}",
                    f"{metrics['min_duration_ms']:.2f}",
                    f"{metrics['max_duration_ms']:.2f}",
                ])
        
        # Step metrics CSV
        step_csv_path = output_path.parent / f"{output_path.stem}_steps.csv"
        with open(step_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Step Type", "Count", "Avg Latency (ms)", 
                "Min Latency (ms)", "Max Latency (ms)"
            ])
            
            for step_type, metrics in insights["step_metrics"]["step_type_avg_latencies"].items():
                writer.writerow([
                    step_type,
                    metrics["count"],
                    f"{metrics['avg_ms']:.2f}",
                    f"{metrics['min_ms']:.2f}",
                    f"{metrics['max_ms']:.2f}",
                ])
        
        print(f"✅ Exported CSV files:")
        print(f"   - {tool_csv_path}")
        print(f"   - {step_csv_path}")


def analyze_traces(traces_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze all traces.
    
    Args:
        traces_dir: Optional path to traces directory
    
    Returns:
        Insights dictionary
    """
    analyzer = TraceAnalyzer(traces_dir)
    return analyzer.analyze_all_traces()

