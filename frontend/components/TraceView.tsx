"use client";

import { useState } from "react";

interface TraceStep {
  step: number;
  title: string;
  description: string;
  status: "completed" | "skipped";
  details?: string;
}

interface TraceViewProps {
  trace: any;
}

export default function TraceView({ trace }: TraceViewProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Build execution path from trace data
  const buildExecutionPath = (): TraceStep[] => {
    const steps: TraceStep[] = [];

    // Step 1: Input Classification
    if (trace?.input_classifier) {
      const cls = trace.input_classifier;
      const intent = cls.intent || "unknown";
      const intentMap: Record<string, string> = {
        drug_info: "understanding your question about a medication",
        drug_interaction: "understanding your question about mixing medications",
        dosage: "understanding your question about how much to take",
        side_effects: "understanding your question about side effects",
        general: "understanding your general question",
      };
      steps.push({
        step: 1,
        title: "Understanding Your Question",
        description: intentMap[intent] || "understanding your question",
        status: "completed",
        details: `I recognized you're ${intentMap[intent] || "asking a question"}.`,
      });
    }

    // Step 2: Safety Check
    if (trace?.safety_advisor) {
      const safety = trace.safety_advisor;
      const riskLevel = safety.risk_level || "unknown";
      let description = "checking if it's safe to answer";
      if (riskLevel === "low") {
        description = "confirmed this is safe to answer";
      } else if (riskLevel === "medium") {
        description = "noted this needs some caution";
      } else if (riskLevel === "high") {
        description = "identified this as high risk";
      }
      steps.push({
        step: 2,
        title: "Safety Check",
        description: description,
        status: "completed",
        details: safety.summary || `I made sure your question was safe to answer.`,
      });
    }

    // Step 3: Medical Research
    if (trace?.medical_reasoning) {
      const med = trace.medical_reasoning;
      const citationCount = med.citations?.length || 0;
      steps.push({
        step: 3,
        title: "Looking Up Information",
        description:
          citationCount > 0
            ? `found information from ${citationCount} trusted source${citationCount > 1 ? "s" : ""}`
            : "searched trusted medical sources",
        status: "completed",
        details:
          citationCount > 0
            ? `I looked up what trusted medical sources say about this topic and found ${citationCount} reliable source${citationCount > 1 ? "s" : ""}.`
            : "I searched trusted medical sources to find accurate information.",
      });
    }

    // Step 4: Making it Easy to Understand
    if (trace?.pharma_miku) {
      steps.push({
        step: 4,
        title: "Making it Easy to Understand",
        description: "explained it in simple language",
        status: "completed",
        details:
          "I rewrote the medical information in simple, everyday language so it's easy to understand.",
      });
    }

    // Step 5: Final Safety Check
    if (trace?.judge) {
      const judge = trace.judge;
      steps.push({
        step: 5,
        title: "Double-Checking Everything",
        description: "verified everything is safe and accurate",
        status: "completed",
        details:
          judge.verdict === "SAFE"
            ? "I double-checked everything to make sure it's safe, accurate, and easy to understand."
            : "I reviewed the answer one more time to ensure it's appropriate.",
      });
    }

    return steps;
  };

  const executionPath = buildExecutionPath();

  if (executionPath.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 border-t border-gray-200 pt-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between text-sm text-gray-600 hover:text-gray-800 transition-colors"
      >
        <span className="flex items-center gap-2">
          <span className="text-lg">🔍</span>
          <span className="font-medium">
            {isExpanded ? "Hide" : "Show"} how I found this information
          </span>
        </span>
        <span className={`transition-transform ${isExpanded ? "rotate-180" : ""}`}>
          ▼
        </span>
      </button>

      {isExpanded && (
        <div className="mt-4 space-y-3">
          <p className="text-xs text-gray-500 mb-4">
            Here's the step-by-step process I followed to answer your question:
          </p>
          {executionPath.map((step, index) => (
            <div key={step.step} className="relative">
              <div className="flex gap-3 p-3 bg-gray-50 rounded-lg border border-gray-100">
                {/* Step Number */}
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#39C5BB] text-white flex items-center justify-center font-semibold text-sm">
                  {step.step}
                </div>

                {/* Step Content */}
                <div className="flex-1">
                  <h4 className="font-medium text-gray-800 text-sm mb-1">
                    {step.title}
                  </h4>
                  <p className="text-xs text-gray-600 mb-1">{step.description}</p>
                  {step.details && (
                    <p className="text-xs text-gray-500 italic">{step.details}</p>
                  )}
                </div>
              </div>

              {/* Connector Line (except for last item) */}
              {index < executionPath.length - 1 && (
                <div className="absolute left-4 top-11 w-0.5 h-3 bg-[#39C5BB] opacity-30"></div>
              )}
            </div>
          ))}

          {/* Citations if available */}
          {trace?.citations && trace.citations.length > 0 && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-100">
              <h4 className="font-medium text-blue-900 text-sm mb-2">
                📚 Sources I Used:
              </h4>
              <ul className="space-y-1">
                {trace.citations.slice(0, 3).map((url: string, idx: number) => (
                  <li key={idx}>
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:text-blue-800 underline break-all"
                    >
                      {url}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

