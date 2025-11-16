"use client";

import { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from "recharts";
import { fetchInsights, Insights } from "../utils/insights";

const COLORS = {
  primary: "#39C5BB",
  secondary: "#FFB7D5",
  accent: "#2fa89f",
  error: "#ef4444",
  warning: "#f59e0b",
  success: "#10b981",
};

const CHART_COLORS = [COLORS.primary, COLORS.secondary, COLORS.accent, "#a855f7", "#f59e0b"];

export default function InsightsPage({ onBack }: { onBack: () => void }) {
  const [insights, setInsights] = useState<Insights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadInsights();
  }, []);

  const loadInsights = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInsights();
      setInsights(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load insights");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#39C5BB] mx-auto mb-4"></div>
          <p className="text-gray-600">Loading insights...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <button
            onClick={loadInsights}
            className="px-4 py-2 bg-[#39C5BB] text-white rounded-lg hover:bg-[#2fa89f] transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!insights) {
    return null;
  }

  const { summary, tool_metrics, step_metrics, shortcuts, error_patterns, bottlenecks, recommendations } = insights;

  // Prepare data for charts
  const toolUsageData = Object.entries(tool_metrics.most_used_tools)
    .slice(0, 10)
    .map(([tool, count]) => ({
      tool: tool.length > 15 ? tool.substring(0, 15) + "..." : tool,
      count,
      fullTool: tool,
    }));

  const toolSuccessData = Object.entries(tool_metrics.tool_success_rates)
    .map(([tool, metrics]) => ({
      tool: tool.length > 15 ? tool.substring(0, 15) + "..." : tool,
      successRate: metrics.success_rate * 100,
      fullTool: tool,
    }))
    .sort((a, b) => b.successRate - a.successRate)
    .slice(0, 10);

  const stepTypeData = Object.entries(step_metrics.step_type_distribution).map(([type, count]) => ({
    type: type.replace("_", " "),
    count,
  }));

  const stepLatencyData = Object.entries(step_metrics.step_type_avg_latencies).map(([type, metrics]) => ({
    type: type.replace("_", " "),
    avgLatency: metrics.avg_ms,
    count: metrics.count,
  }));

  const errorData = Object.entries(error_patterns.most_common_errors)
    .slice(0, 5)
    .map(([error, count]) => ({
      error: error.length > 30 ? error.substring(0, 30) + "..." : error,
      count,
      fullError: error,
    }));

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-2">
              <span className="text-[#39C5BB]">Agent</span>{" "}
              <span className="text-[#FFB7D5]">Insights</span>
            </h1>
            <p className="text-gray-600">
              Behavioral analysis and performance metrics
            </p>
          </div>
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            ← Back to Chat
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-[#39C5BB]">
            <div className="text-sm text-gray-600 mb-1">Total Traces</div>
            <div className="text-3xl font-bold text-gray-800">{summary.total_traces}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-[#10b981]">
            <div className="text-sm text-gray-600 mb-1">Success Rate</div>
            <div className="text-3xl font-bold text-gray-800">
              {(summary.overall_success_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-[#f59e0b]">
            <div className="text-sm text-gray-600 mb-1">Shortcut Rate</div>
            <div className="text-3xl font-bold text-gray-800">
              {(shortcuts.shortcut_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-[#ef4444]">
            <div className="text-sm text-gray-600 mb-1">Total Errors</div>
            <div className="text-3xl font-bold text-gray-800">{summary.total_errors}</div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Tool Usage Chart */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Most Used Tools</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={toolUsageData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="tool" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill={COLORS.primary} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Tool Success Rates */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Tool Success Rates</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={toolSuccessData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="tool" angle={-45} textAnchor="end" height={100} />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                <Bar dataKey="successRate" fill={COLORS.success} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Step Type Distribution */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Step Type Distribution</h2>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={stepTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ type, percent }) => `${type}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {stepTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Step Latency */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Average Latency by Step Type</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stepLatencyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip formatter={(value: number) => `${value.toFixed(0)}ms`} />
                <Bar dataKey="avgLatency" fill={COLORS.accent} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Error Patterns */}
        {errorData.length > 0 && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Most Common Errors</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={errorData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="error" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill={COLORS.error} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Bottlenecks & Recommendations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Bottlenecks */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Bottlenecks & Risk Points</h2>
            <div className="space-y-4">
              {bottlenecks.slow_steps.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">Slow Steps</h3>
                  <ul className="space-y-2">
                    {bottlenecks.slow_steps.map((step, idx) => (
                      <li key={idx} className="text-sm text-gray-600">
                        <span className="font-medium">{step.step_type}</span>:{" "}
                        {step.avg_latency_ms.toFixed(0)}ms ({step.count} occurrences)
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {bottlenecks.unreliable_tools.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">Unreliable Tools</h3>
                  <ul className="space-y-2">
                    {bottlenecks.unreliable_tools.map((tool, idx) => (
                      <li key={idx} className="text-sm text-gray-600">
                        <span className="font-medium">{tool.tool}</span>:{" "}
                        {(tool.success_rate * 100).toFixed(1)}% success ({tool.total_calls} calls)
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {bottlenecks.high_error_tools.length > 0 && (
                <div>
                  <h3 className="font-semibold text-gray-700 mb-2">High Error Tools</h3>
                  <ul className="space-y-2">
                    {bottlenecks.high_error_tools.map((tool, idx) => (
                      <li key={idx} className="text-sm text-gray-600">
                        <span className="font-medium">{tool.tool}</span>: {tool.error_count} errors
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {bottlenecks.slow_steps.length === 0 &&
                bottlenecks.unreliable_tools.length === 0 &&
                bottlenecks.high_error_tools.length === 0 && (
                  <p className="text-sm text-gray-500 italic">No significant bottlenecks detected</p>
                )}
            </div>
          </div>

          {/* Recommendations */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Recommendations</h2>
            <ul className="space-y-3">
              {recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-3">
                  <span className="text-[#39C5BB] font-bold mt-1">•</span>
                  <span className="text-sm text-gray-700">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Shortcuts */}
        {shortcuts.total_suspected > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              ⚠️ Shortcut Detection ({shortcuts.total_suspected} traces)
            </h2>
            <p className="text-sm text-gray-700 mb-4">
              {shortcuts.total_suspected} traces contain suspected shortcuts where answers may contain
              factual claims without supporting tool calls.
            </p>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {shortcuts.traces_with_shortcuts.slice(0, 5).map((trace, idx) => (
                <div key={idx} className="bg-white rounded p-3 text-sm">
                  <span className="font-medium">Session {trace.session_id.substring(0, 8)}...</span>:{" "}
                  {trace.details.reason}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Refresh Button */}
        <div className="text-center">
          <button
            onClick={loadInsights}
            className="px-6 py-2 bg-[#39C5BB] text-white rounded-lg hover:bg-[#2fa89f] transition-colors"
          >
            🔄 Refresh Insights
          </button>
        </div>
      </div>
    </div>
  );
}

