# 🏥 PharmaMiku - Glass Box AI Pharmacy Assistant

> An intelligent, transparent pharmacy consultation assistant powered by Claude 3.5 Sonnet via AWS Bedrock, featuring complete traceability and multi-agent reasoning.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16.0-black.svg)](https://nextjs.org/)
[![Claude](https://img.shields.io/badge/Claude-3.5%20Sonnet-purple.svg)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 Overview

PharmaMiku is a **Glass Box AI Agent** that provides reliable pharmaceutical information with complete transparency. Unlike traditional black-box AI systems, every decision, tool call, and reasoning step is logged, traceable, and explainable. Built for hackathons and production use, this system demonstrates best practices in AI agent development.

### ✨ Key Features

- 🤖 **Multi-Agent Architecture** - 6 specialized agents working together
- 🔍 **Complete Traceability** - Every step logged and visible
- 🛠️ **Dynamic Tool System** - Extensible tools for calculations, drug info, reminders, and summarization
- 📊 **Behavioral Insights** - Analytics on agent performance and patterns
- 🎨 **Modern UI** - React/Next.js frontend with real-time trace visualization
- ⚡ **Streaming Responses** - Real-time progress updates via Server-Sent Events
- 🔒 **Safety-First Design** - Multiple safety checks and risk assessment layers
- 📈 **Observability Dashboard** - Visual insights into agent behavior and failures

### ⚠️ Important Disclaimer

This agent provides **general pharmaceutical information only**. Always consult with a qualified healthcare provider for medical advice, diagnoses, or treatment decisions.

---

## 🏗️ Tech Stack

### Backend
- **Python 3.11+** - Core language
- **FastAPI** - Modern async web framework
- **Pydantic** - Data validation and models
- **AWS Bedrock** - Claude 3.5 Sonnet LLM access
- **Valyu DeepSearch** - Medical evidence retrieval (optional)
- **httpx** - Async HTTP client with connection pooling

### Frontend
- **Next.js 16** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first styling
- **Recharts** - Data visualization
- **React Icons** - Icon library

### Observability & Tools
- **Custom Trace Manager** - JSON-based trace storage
- **LangSmith Integration** - Optional external observability
- **Dynamic Tool System** - Pluggable tool architecture
- **Behavioral Insights** - Pattern analysis and metrics

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18+ and npm
- API credentials (see Environment Variables)

### Installation

#### 1. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r newrequirements.txt
```

#### 2. Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Required: Holistic AI / AWS Bedrock
HOLISTIC_AI_TEAM_ID=your_team_id
HOLISTIC_AI_API_TOKEN=your_api_token
HOLISTIC_AI_API_URL=your_api_gateway_url

# Optional: Valyu for medical evidence
VALYU_API_KEY=your_valyu_key

# Optional: LangSmith for observability
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=pharmamiku

# Optional: Debug mode
DEBUG_TRACE=true
```

#### 3. Start Backend Server

```bash
cd backend
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

#### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

---

## 📁 Project Structure

```
pharmacy/
├── backend/
│   ├── agents/              # Multi-agent system
│   │   ├── orchestrator.py  # Main pipeline coordinator
│   │   ├── input_classifier.py
│   │   ├── safety_advisor.py
│   │   ├── medical_reasoning_agent.py
│   │   ├── pharma_miku_agent.py
│   │   ├── judge.py
│   │   ├── trace_explainer.py
│   │   └── tool_decision_agent.py
│   ├── tools/               # Dynamic tool system
│   │   ├── base_tool.py
│   │   ├── tool_manager.py
│   │   ├── calculator_tool.py
│   │   ├── drug_info_tool.py
│   │   ├── reminder_tool.py
│   │   └── summarizer_tool.py
│   ├── observability/       # Trace and insights
│   │   ├── trace_manager.py
│   │   └── insights.py
│   ├── utils/              # Utilities
│   │   └── cache.py
│   ├── server.py           # FastAPI application
│   ├── main.py            # Entry point
│   └── traces/             # Trace JSON files
│
├── frontend/
│   ├── app/               # Next.js App Router
│   │   ├── page.tsx      # Main chat interface
│   │   └── layout.tsx
│   ├── components/        # React components
│   │   ├── ChatBox.tsx
│   │   ├── ChatMessage.tsx
│   │   ├── TraceView.tsx
│   │   ├── TracePage.tsx
│   │   ├── InsightsPage.tsx
│   │   ├── LiveTraceWidget.tsx
│   │   └── Sidebar.tsx
│   ├── utils/            # Frontend utilities
│   │   ├── api.ts        # API client
│   │   └── useTrace.ts   # Trace hook
│   └── package.json
│
└── README.md
```

---

## 🎯 How It Works

PharmaMiku uses a **6-agent pipeline** to process user queries:

1. **Input Classifier** - Understands user intent and context
2. **Safety Advisor** - Assesses risk and safety concerns
3. **Tool Decision Agent** - Decides which tools to use (if any)
4. **Medical Reasoning Agent** - Retrieves evidence and generates medical answer
5. **PharmaMiku Agent** - Applies persona and makes answer user-friendly
6. **Judge Agent** - Final safety and quality check
7. **Trace Explainer** - Generates human-readable reasoning explanation

Every step is logged to a trace file (`traces/{session_id}.json`) for complete observability.

**📚 For detailed technical documentation, see [TECHNICAL_GUIDE.md](./TECHNICAL_GUIDE.md)**

---

## 🔌 API Endpoints

### Chat Endpoint
```http
POST /ask
Content-Type: application/json

{
  "message": "What is ibuprofen used for?"
}
```

**Response:** Server-Sent Events (SSE) stream with progress updates and final answer.

### Trace Endpoint
```http
GET /trace/{session_id}
```

Returns complete trace JSON for a session.

### Insights Endpoint
```http
GET /insights
GET /insights?format=report
```

Returns behavioral insights and analytics from all traces.

---

## 🛠️ Available Tools

The system includes these dynamic tools:

- **CalculatorTool** - Mathematical calculations
- **DrugInfoTool** - Drug information lookup
- **ReminderTool** - Schedule medication reminders
- **SummarizerTool** - AI-powered text summarization

Tools are registered dynamically and can be extended easily.

---

## 📊 Observability Features

### Trace System
- Every agent step logged with timestamps
- Tool calls with input/output
- Memory/state updates
- Decision reasoning
- Error tracking

### Behavioral Insights
- Tool usage patterns
- Success/failure rates
- Latency metrics
- Shortcut detection
- Failure analysis

### Frontend Dashboard
- Real-time trace visualization
- Insights page with charts
- Failure analysis view
- Session management

---

## 🧪 Example Questions

- "What is ibuprofen used for?"
- "Can I take paracetamol with warfarin?"
- "Calculate: 500mg twice daily for 7 days"
- "What are the side effects of aspirin?"
- "Summarize the drug instructions for paracetamol"

---

## 🔧 Configuration

### Debug Mode

Set `DEBUG_TRACE=true` in `.env` to:
- Print all trace steps to console
- Save detailed trace JSON files
- Enable verbose logging

### Caching

Responses are cached by default to improve performance. Cache is stored in-memory.

---

## 📝 License

MIT License - see LICENSE file for details

---

## 🤝 Contributing

This is a hackathon project. Feel free to fork, modify, and extend!

---

## 📚 Additional Documentation

- **[TECHNICAL_GUIDE.md](./TECHNICAL_GUIDE.md)** - Detailed architecture and execution flow
- **[API Documentation](./docs/API.md)** - Complete API reference (coming soon)

---

## 🙏 Acknowledgments

- Built for **The Great Agent Hack 2025**
- Powered by **Claude 3.5 Sonnet** via AWS Bedrock
- Medical evidence via **Valyu DeepSearch** (optional)
