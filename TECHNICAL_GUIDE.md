# 🔬 PharmaMiku Technical Guide

> Complete technical documentation for understanding the PharmaMiku Glass Box AI Agent system

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Agent Pipeline](#agent-pipeline)
3. [Execution Flow](#execution-flow)
4. [Trace System](#trace-system)
5. [Tool System](#tool-system)
6. [Observability](#observability)
7. [Frontend Architecture](#frontend-architecture)
8. [Data Flow](#data-flow)

---

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────┐
│   User      │
│  (Browser)  │
└──────┬──────┘
       │ HTTP/SSE
       ▼
┌─────────────────────────────────┐
│      FastAPI Backend            │
│  ┌───────────────────────────┐  │
│  │    Orchestrator           │  │
│  │  ┌─────────────────────┐ │  │
│  │  │ Agent 1: Classifier  │ │  │
│  │  │ Agent 2: Safety      │ │  │
│  │  │ Agent 3: Medical     │ │  │
│  │  │ Agent 4: Persona     │ │  │
│  │  │ Agent 5: Judge       │ │  │
│  │  │ Agent 6: Explainer   │ │  │
│  │  └─────────────────────┘ │  │
│  │  ┌─────────────────────┐ │  │
│  │  │  Tool Manager        │ │  │
│  │  │  - Calculator        │ │  │
│  │  │  - Drug Info        │ │  │
│  │  │  - Reminder         │ │  │
│  │  │  - Summarizer       │ │  │
│  │  └─────────────────────┘ │  │
│  │  ┌─────────────────────┐ │  │
│  │  │  Trace Manager       │ │  │
│  │  │  - Log all steps    │ │  │
│  │  │  - Save to JSON     │ │  │
│  │  └─────────────────────┘ │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   External Services             │
│  - AWS Bedrock (Claude 3.5)    │
│  - Valyu DeepSearch (optional) │
└─────────────────────────────────┘
```

### Component Layers

1. **Frontend Layer** (React/Next.js)
   - User interface
   - Real-time trace visualization
   - Insights dashboard

2. **API Layer** (FastAPI)
   - REST endpoints
   - Server-Sent Events (SSE) streaming
   - Request/response handling

3. **Orchestration Layer** (Orchestrator)
   - Coordinates all agents
   - Manages execution flow
   - Handles state transitions

4. **Agent Layer** (6 Specialized Agents)
   - Each agent has a specific responsibility
   - Agents pass data sequentially
   - All actions are logged

5. **Tool Layer** (Dynamic Tools)
   - Extensible tool system
   - Async execution
   - Integrated with trace system

6. **Observability Layer** (Trace Manager)
   - Logs every step
   - Generates insights
   - Stores traces persistently

---

## 🤖 Agent Pipeline

### Agent 1: Input Classifier

**File:** `backend/agents/input_classifier.py`

**Purpose:** Understands user intent and extracts context

**What it does:**
- Analyzes the user's question
- Classifies intent (drug_info, drug_interaction, general_question)
- Detects age group (child, teen, adult, elderly)
- Assesses initial risk level (low, medium, high)
- Determines if handoff to human is needed

**Output:**
```python
InputClassification(
    intent="drug_info",
    query_type="drug_info",
    risk_level="low",
    needs_handoff=False,
    explanation="User asking about drug information",
    age_group="adult"
)
```

**LLM Call:** Yes (Claude 3.5 Sonnet)

---

### Agent 2: Safety Advisor

**File:** `backend/agents/safety_advisor.py`

**Purpose:** Evaluates safety risks and determines if query should proceed

**What it does:**
- Takes classification from Agent 1
- Evaluates safety risk based on user input
- Determines risk level (low, medium, high)
- Decides if medical handoff is required
- Can block dangerous queries early

**Output:**
```python
SafetyAssessment(
    risk_level="low",
    needs_handoff=False,
    safety_decision="ALLOW",
    reasoning="Query is safe to proceed"
)
```

**LLM Call:** Yes (Claude 3.5 Sonnet)

**Early Exit:** If `risk_level == "high"` and `needs_handoff == True`, the pipeline stops and returns a safety message.

---

### Agent 2.5: Tool Decision Agent

**File:** `backend/agents/tool_decision_agent.py`

**Purpose:** Decides which tools (if any) should be called

**What it does:**
- Analyzes user request
- Checks available tools
- Determines if a tool is needed
- Selects appropriate tool
- Extracts tool arguments from user input

**Available Tools:**
- `calculator` - Math calculations
- `drug_info` - Drug information lookup
- `reminder` - Schedule reminders
- `summarizer` - Text summarization

**Output:**
```python
ToolDecision(
    tool_name="drug_info",
    arguments={"drug_name": "paracetamol"},
    should_use_tool=True,
    reasoning="User asked for drug information"
)
```

**LLM Call:** Yes (Claude 3.5 Sonnet)

**Tool Execution:** If `should_use_tool == True`, the selected tool is executed asynchronously.

---

### Agent 3: Medical Reasoning Agent

**File:** `backend/agents/medical_reasoning_agent.py`

**Purpose:** Generates evidence-based medical answers

**What it does:**
1. **Evidence Retrieval** (if Valyu is configured):
   - Searches Valyu DeepSearch for medical evidence
   - Retrieves top 5 relevant sources
   - Extracts citations and URLs

2. **Medical Answer Generation**:
   - Takes user input + classification + safety assessment
   - Includes evidence from Valyu (if available)
   - Uses Claude 3.5 Sonnet to generate canonical medical answer
   - Includes warnings and safety information

**Output:**
```python
MedicalAnswer(
    canonical_answer="Ibuprofen is a nonsteroidal anti-inflammatory drug...",
    warnings="May cause stomach upset. Avoid if allergic to NSAIDs.",
    citations=["https://example.com/ibuprofen"],
    evidence=[EvidenceItem(...)]
)
```

**LLM Call:** Yes (Claude 3.5 Sonnet)

**External API:** Valyu DeepSearch (optional)

---

### Agent 4: PharmaMiku Persona Agent

**File:** `backend/agents/pharma_miku_agent.py`

**Purpose:** Transforms medical answer into user-friendly, accessible format

**What it does:**
- Takes canonical medical answer from Agent 3
- Adapts tone based on age group
- Makes language clear and accessible
- Adds kawaii/cute personality
- Formats with bullet points for readability
- Includes safety reminders
- Preserves all medical facts (doesn't change them)

**Output:**
```python
UserFacingAnswer(
    text="💊 Hey there! Ibuprofen is a medication that helps with...",
    citations=["https://example.com/ibuprofen"]
)
```

**LLM Call:** Yes (Claude 3.5 Sonnet)

**Key Constraint:** Must NOT change medical facts, only presentation.

---

### Agent 5: Judge Agent

**File:** `backend/agents/judge.py`

**Purpose:** Final safety and quality check

**What it does:**
- Reviews the user-facing answer
- Compares with canonical medical answer
- Checks for safety issues
- Verifies answer quality
- Can modify or flag the answer
- Returns verdict (APPROVE, MODIFY, REJECT)

**Output:**
```python
JudgeVerdict(
    verdict="APPROVE",
    quality_score=0.95,
    safety_concerns=[],
    reasoning="Answer is safe and accurate"
)
```

**LLM Call:** Yes (Claude 3.5 Sonnet)

**Action:** Applies verdict to final answer (may add warnings or modify text).

---

### Agent 6: Trace Explainer Agent

**File:** `backend/agents/trace_explainer.py`

**Purpose:** Generates human-readable explanation of the reasoning process

**What it does:**
- Takes the complete trace
- Analyzes all steps taken
- Generates user-friendly explanation
- Explains how the answer was found
- Shows the reasoning path

**Output:**
```python
TraceExplanation(
    trace_explanation_user_friendly="I found this information by first classifying your question, then searching medical databases, and finally formatting it in a way that's easy to understand...",
    technical_summary="Classification: drug_info, Safety: low risk, Tools: drug_info, Medical reasoning: 3 citations found"
)
```

**LLM Call:** Yes (Claude 3.5 Sonnet)

**Final Step:** This explanation is appended to the final answer.

---

## 🔄 Execution Flow

### Step-by-Step Pipeline

```
1. User sends message
   │
   ▼
2. FastAPI receives request
   │
   ▼
3. Orchestrator.run_with_progress()
   │
   ├─► Start trace session
   │
   ├─► Agent 1: Input Classifier
   │   ├─► Log decision step
   │   ├─► Call LLM
   │   ├─► Log tool call result
   │   └─► Update state
   │
   ├─► Agent 2: Safety Advisor
   │   ├─► Log decision step
   │   ├─► Call LLM
   │   ├─► Log tool call result
   │   ├─► Update state
   │   └─► Check: High risk? → Early exit
   │
   ├─► Agent 2.5: Tool Decision
   │   ├─► Log decision step
   │   ├─► Call LLM
   │   ├─► Log decision result
   │   └─► If tool needed:
   │       ├─► Execute tool (async)
   │       ├─► Log tool call
   │       └─► Update state
   │
   ├─► Agent 3: Medical Reasoning
   │   ├─► Fetch evidence (Valyu)
   │   ├─► Call LLM with evidence
   │   ├─► Log tool call result
   │   └─► Update state
   │
   ├─► Agent 4: PharmaMiku Persona
   │   ├─► Log decision step
   │   ├─► Call LLM
   │   ├─► Log tool call result
   │   └─► Update state
   │
   ├─► Agent 5: Judge
   │   ├─► Log decision step
   │   ├─► Call LLM
   │   ├─► Log tool call result
   │   ├─► Apply verdict
   │   └─► Update state
   │
   ├─► Agent 6: Trace Explainer
   │   ├─► Log decision step
   │   ├─► Call LLM
   │   ├─► Log tool call result
   │   └─► Append explanation to answer
   │
   ├─► End trace session
   │
   └─► Return final answer + trace
```

### State Transitions

The system maintains a `current_state` dictionary that evolves through the pipeline:

```python
# Initial state
{
    "user_input": "...",
    "stage": "initialized"
}

# After Agent 1
{
    "user_input": "...",
    "classification": {...},
    "age_group": "adult",
    "stage": "classified"
}

# After Agent 2
{
    "user_input": "...",
    "classification": {...},
    "safety": {...},
    "stage": "safety_evaluated"
}

# After Tools (if used)
{
    ...,
    "tool_results": [...],
    "stage": "tools_executed"
}

# After Agent 3
{
    ...,
    "medical_answer": {...},
    "stage": "medical_reasoning_complete"
}

# After Agent 4
{
    ...,
    "user_facing_answer": {...},
    "stage": "persona_applied"
}

# After Agent 5
{
    ...,
    "judge_verdict": {...},
    "final_answer": "...",
    "citations": [...],
    "stage": "judged"
}
```

Each state transition is logged as a `memory_update` step in the trace.

---

## 📊 Trace System

### Trace Structure

Every execution creates a trace JSON file: `traces/{session_id}.json`

```json
{
  "session_id": "uuid-here",
  "started_at": "2024-01-01T12:00:00",
  "ended_at": "2024-01-01T12:00:05",
  "steps": [
    {
      "step_id": 1,
      "type": "decision",
      "timestamp": "2024-01-01T12:00:00.100",
      "input": {"user_input": "...", "stage": "classification"},
      "output": {
        "reasoning": "Starting input classification...",
        "selected_action": "classify_input"
      },
      "metadata": {
        "agent": "InputClassifier",
        "step": 1
      },
      "success": true
    },
    {
      "step_id": 2,
      "type": "tool_call",
      "timestamp": "2024-01-01T12:00:00.500",
      "input": {"user_input": "..."},
      "output": {
        "intent": "drug_info",
        "query_type": "drug_info",
        "risk_level": "low"
      },
      "tool_name": "classify_input",
      "duration_ms": 400.5,
      "metadata": {
        "agent": "InputClassifier",
        "duration_ms": 400.5,
        "summary": "Classified as: drug_info"
      },
      "success": true
    },
    {
      "step_id": 3,
      "type": "memory_update",
      "timestamp": "2024-01-01T12:00:00.600",
      "input": {
        "user_input": "...",
        "stage": "initialized"
      },
      "output": {
        "old_state": {...},
        "new_state": {...},
        "diff": {...},
        "cause": "classification_result"
      },
      "metadata": {
        "agent": "InputClassifier"
      },
      "success": true
    }
    // ... more steps
  ],
  "metadata": {
    "total_steps": 25,
    "total_tool_calls": 8,
    "total_decisions": 6,
    "total_memory_updates": 7,
    "duration_seconds": 5.2
  }
}
```

### Step Types

1. **`decision`** - Agent decision step
   - Contains reasoning and selected action
   - Logged before major operations

2. **`tool_call`** - Tool or agent execution
   - Contains input, output, duration
   - Includes tool name (if applicable)
   - Success/error status

3. **`memory_update`** - State transition
   - Contains old_state, new_state, diff
   - Shows what changed and why

### Trace Manager API

```python
from observability import get_trace_manager, StepType

trace_manager = get_trace_manager()

# Start trace
session_id = trace_manager.start_trace()

# Log decision
trace_manager.append_decision(
    session_id=session_id,
    input_state={...},
    reasoning="...",
    selected_action="...",
    metadata={...}
)

# Log tool call
trace_manager.append_trace(
    session_id=session_id,
    step_type=StepType.TOOL_CALL,
    input_data={...},
    output_data={...},
    tool_name="...",
    duration_ms=123.45,
    success=True,
    metadata={...}
)

# Log memory update
trace_manager.append_memory_update(
    session_id=session_id,
    old_state={...},
    new_state={...},
    cause="...",
    metadata={...}
)

# End trace
trace = trace_manager.end_trace(session_id)
```

---

## 🛠️ Tool System

### Architecture

The tool system is **dynamic and extensible**:

```
ToolManager (Singleton)
  ├─► Tools Registry (Dict[str, BaseTool])
  │
  └─► execute_tool()
      ├─► Validates tool exists
      ├─► Validates arguments
      ├─► Executes tool (async)
      ├─► Logs to trace
      └─► Returns ToolResult
```

### Base Tool Interface

All tools inherit from `BaseTool`:

```python
class BaseTool(ABC):
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON schema
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool asynchronously"""
        pass
```

### Available Tools

#### 1. CalculatorTool
- **Purpose:** Mathematical calculations
- **Input:** `expression: str` (e.g., "500 * 2")
- **Output:** Numeric result
- **Use Case:** Dosage calculations, quantity math

#### 2. DrugInfoTool
- **Purpose:** Drug information lookup
- **Input:** `drug_name: str`
- **Output:** Drug data (uses, dosage, side effects, instructions)
- **Use Case:** Quick drug information retrieval
- **Note:** Currently uses mock data (can be extended to real API)

#### 3. ReminderTool
- **Purpose:** Schedule medication reminders
- **Input:** `message: str`, `time_in_minutes: int` or `datetime_str: str`
- **Output:** Scheduled reminder confirmation
- **Use Case:** Help users remember medication times
- **Note:** Currently mock (can integrate with APScheduler/Celery)

#### 4. SummarizerTool
- **Purpose:** AI-powered text summarization
- **Input:** `text: str`, `max_length: int`, `focus: str`
- **Output:** Summarized text
- **Use Case:** Summarize long drug instructions
- **LLM Call:** Yes (Claude 3.5 Sonnet)

### Tool Execution Flow

```
1. ToolDecisionAgent decides tool is needed
   │
   ▼
2. ToolManager.execute_tool() called
   │
   ├─► Validate tool exists
   │
   ├─► Validate arguments match schema
   │
   ├─► Start timer
   │
   ├─► Execute tool.execute() (async)
   │   │
   │   └─► Tool does its work
   │
   ├─► Stop timer
   │
   ├─► Log to trace:
   │   ├─► tool_name
   │   ├─► arguments
   │   ├─► output
   │   ├─► duration_ms
   │   ├─► success/error
   │   └─► metadata
   │
   └─► Return ToolResult
```

### Adding New Tools

1. Create tool class:
```python
# backend/tools/my_tool.py
from .base_tool import BaseTool, ToolResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    parameters = {
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        },
        "required": ["input"]
    }
    
    async def execute(self, input: str) -> ToolResult:
        # Do work
        result = process(input)
        return ToolResult(
            success=True,
            output=result
        )
```

2. Register in orchestrator:
```python
# backend/agents/orchestrator.py
from tools.my_tool import MyTool

def _register_tools(self):
    self.tool_manager.register_tool(MyTool())
```

3. ToolDecisionAgent will automatically discover it!

---

## 📈 Observability

### Trace Storage

- **Location:** `backend/traces/{session_id}.json`
- **Format:** JSON with structured steps
- **Persistence:** Saved on trace end
- **Debug Mode:** Also prints to console if `DEBUG_TRACE=true`

### Behavioral Insights

The system analyzes all traces to find patterns:

**Metrics Calculated:**
- Total traces analyzed
- Average tool success rate
- Shortcut rate (answers without tool calls)
- Average latency per step type
- Most used tools
- Failure rates per tool/model

**Failure Analysis:**
- Identifies errors and exceptions
- Attributes root causes (LLM, tool, memory, user_input)
- Suggests remediation actions
- Tracks recurring failures

**Access:**
- API: `GET /insights`
- Frontend: Insights page with charts

### Frontend Observability

1. **Live Trace Widget**
   - Real-time trace visualization
   - Updates every 500ms
   - Filterable by step type
   - Expandable step details

2. **Trace Page**
   - Full trace for a session
   - Shows prompt and complete execution
   - Timeline view
   - Step-by-step breakdown

3. **Insights Page**
   - Charts and metrics
   - Tool usage patterns
   - Failure analysis
   - Performance trends

---

## 🎨 Frontend Architecture

### Component Structure

```
app/page.tsx (Main)
  ├─► Sidebar
  │   ├─► Chat history
  │   ├─► Live Trace button
  │   ├─► View Trace button
  │   └─► View Insights button
  │
  ├─► Chat Area
  │   ├─► ChatMessage (per message)
  │   ├─► TraceView (if trace available)
  │   └─► DocumentSummary (if document uploaded)
  │
  ├─► ChatBox
  │   └─► Input + Send button
  │
  ├─► LiveTraceWidget (conditional)
  │   └─► Real-time trace updates
  │
  ├─► TracePage (conditional)
  │   └─► Full trace visualization
  │
  └─► InsightsPage (conditional)
      └─► Analytics dashboard
```

### Data Flow (Frontend)

```
1. User types message
   │
   ▼
2. ChatBox calls onSend()
   │
   ▼
3. page.tsx calls askBackend()
   │
   ├─► Shows typing indicator
   │
   ├─► Opens SSE connection
   │
   ├─► Receives progress updates
   │   └─► Updates UI in real-time
   │
   ├─► Receives final response
   │   ├─► Adds message to chat
   │   ├─► Stores trace
   │   └─► Updates session ID
   │
   └─► User can view trace/insights
```

### API Integration

**File:** `frontend/utils/api.ts`

```typescript
// Streaming API call
askBackend(question, onProgress)
  ├─► POST /ask
  ├─► Streams SSE events
  ├─► onProgress() called for each update
  └─► Returns final response

// Trace retrieval
GET /trace/{session_id}
  └─► Returns complete trace JSON

// Insights
GET /insights
  └─► Returns behavioral insights
```

---

## 🔄 Complete Data Flow

### Request Journey

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INPUT                                               │
│    "What is ibuprofen used for?"                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. FRONTEND (React)                                         │
│    - User types in ChatBox                                  │
│    - Clicks send                                            │
│    - Calls askBackend()                                     │
│    - Shows "typing..." indicator                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP POST /ask
                     │ { "message": "..." }
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. FASTAPI SERVER                                           │
│    - Receives request                                       │
│    - Creates session_id                                     │
│    - Starts SSE stream                                      │
│    - Calls Orchestrator.run_with_progress()                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. ORCHESTRATOR                                             │
│    - Starts trace session                                   │
│    - Initializes state                                      │
│    │                                                        │
│    ├─► AGENT 1: Input Classifier                           │
│    │   - LLM call: "Classify this question"                │
│    │   - Returns: intent="drug_info", risk="low"           │
│    │   - Logs: decision + tool_call + memory_update        │
│    │                                                        │
│    ├─► AGENT 2: Safety Advisor                             │
│    │   - LLM call: "Is this safe?"                         │
│    │   - Returns: risk_level="low", needs_handoff=false    │
│    │   - Logs: decision + tool_call + memory_update        │
│    │                                                        │
│    ├─► AGENT 2.5: Tool Decision                            │
│    │   - LLM call: "Do we need a tool?"                    │
│    │   - Returns: tool_name="drug_info"                     │
│    │   - Executes: DrugInfoTool                            │
│    │   - Logs: decision + tool_call + memory_update        │
│    │                                                        │
│    ├─► AGENT 3: Medical Reasoning                          │
│    │   - Calls: Valyu DeepSearch (optional)                │
│    │   - LLM call: "Generate medical answer"               │
│    │   - Returns: canonical_answer + citations             │
│    │   - Logs: tool_call + memory_update                   │
│    │                                                        │
│    ├─► AGENT 4: PharmaMiku Persona                         │
│    │   - LLM call: "Make this user-friendly"               │
│    │   - Returns: user_facing_answer                        │
│    │   - Logs: decision + tool_call + memory_update        │
│    │                                                        │
│    ├─► AGENT 5: Judge                                      │
│    │   - LLM call: "Is this answer safe?"                  │
│    │   - Returns: verdict="APPROVE"                        │
│    │   - Applies verdict to answer                         │
│    │   - Logs: decision + tool_call + memory_update       │
│    │                                                        │
│    └─► AGENT 6: Trace Explainer                            │
│        - LLM call: "Explain the reasoning"                 │
│        - Returns: user_friendly_explanation                 │
│        - Appends to final answer                           │
│        - Logs: decision + tool_call                        │
│                                                        │
│    - Ends trace session                                    │
│    - Saves trace to JSON                                   │
│    - Returns: (final_answer, trace)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ SSE: "data: {type: 'complete', ...}"
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. FRONTEND (React)                                         │
│    - Receives final response                                │
│    - Updates chat message                                   │
│    - Stores trace in state                                  │
│    - User can view trace/insights                           │
└─────────────────────────────────────────────────────────────┘
```

### Trace Flow

```
Every Step:
  ├─► Orchestrator calls trace_manager.append_*()
  │
  ├─► TraceManager:
  │   ├─► Creates step object
  │   ├─► Adds to active_traces[session_id]["steps"]
  │   ├─► Updates metadata (counts, etc.)
  │   └─► If DEBUG_TRACE: prints to console
  │
  └─► At end:
      ├─► trace_manager.end_trace()
      ├─► Calculates duration
      ├─► Saves to traces/{session_id}.json
      └─► Returns complete trace
```

---

## 🎯 Key Design Decisions

### Why 6 Agents?

Each agent has a **single responsibility**:
- **Separation of Concerns:** Each agent does one thing well
- **Testability:** Can test each agent independently
- **Observability:** Clear boundaries for tracing
- **Maintainability:** Easy to modify one agent without affecting others

### Why Trace Everything?

- **Transparency:** Users can see how answers are generated
- **Debugging:** Easy to find where things went wrong
- **Compliance:** Medical AI needs audit trails
- **Learning:** Can analyze patterns and improve

### Why Dynamic Tools?

- **Extensibility:** Add new tools without changing core code
- **Modularity:** Tools are independent components
- **Testability:** Test tools in isolation
- **Flexibility:** Enable/disable tools easily

### Why Streaming?

- **User Experience:** Immediate feedback
- **Perceived Performance:** Feels faster
- **Transparency:** See progress in real-time
- **Debugging:** Can see where pipeline is stuck

---

## 📝 Example Execution

### Input
```
User: "What is ibuprofen used for?"
```

### Trace Output (Simplified)

```json
{
  "session_id": "abc-123",
  "steps": [
    {
      "step_id": 1,
      "type": "decision",
      "agent": "InputClassifier",
      "reasoning": "Starting classification"
    },
    {
      "step_id": 2,
      "type": "tool_call",
      "tool_name": "classify_input",
      "output": {
        "intent": "drug_info",
        "risk_level": "low"
      },
      "duration_ms": 450
    },
    {
      "step_id": 3,
      "type": "memory_update",
      "cause": "classification_result",
      "new_state": {"stage": "classified"}
    },
    {
      "step_id": 4,
      "type": "decision",
      "agent": "SafetyAdvisor",
      "reasoning": "Evaluating safety"
    },
    {
      "step_id": 5,
      "type": "tool_call",
      "tool_name": "evaluate_risk",
      "output": {
        "risk_level": "low",
        "safety_decision": "ALLOW"
      },
      "duration_ms": 380
    },
    {
      "step_id": 6,
      "type": "decision",
      "agent": "ToolDecisionAgent",
      "reasoning": "Deciding if tools needed"
    },
    {
      "step_id": 7,
      "type": "tool_call",
      "tool_name": "drug_info",
      "input": {"drug_name": "ibuprofen"},
      "output": {"data": {...}},
      "duration_ms": 120
    },
    {
      "step_id": 8,
      "type": "tool_call",
      "tool_name": "medical_reasoning",
      "output": {
        "canonical_answer": "Ibuprofen is a nonsteroidal...",
        "citations": ["https://..."]
      },
      "duration_ms": 2500
    },
    {
      "step_id": 9,
      "type": "tool_call",
      "tool_name": "apply_persona",
      "output": {
        "text": "💊 Hey there! Ibuprofen is a medication..."
      },
      "duration_ms": 800
    },
    {
      "step_id": 10,
      "type": "tool_call",
      "tool_name": "judge_evaluate",
      "output": {
        "verdict": "APPROVE",
        "quality_score": 0.95
      },
      "duration_ms": 600
    },
    {
      "step_id": 11,
      "type": "tool_call",
      "tool_name": "explain",
      "output": {
        "trace_explanation_user_friendly": "I found this by..."
      },
      "duration_ms": 700
    }
  ],
  "metadata": {
    "total_steps": 11,
    "duration_seconds": 5.55
  }
}
```

### Final Answer
```
💊 Hey there! Ibuprofen is a medication that helps with pain and inflammation...

[Medical information here...]

---

💭 How I found this information:
I classified your question as a drug information request, checked that it was safe to answer, looked up ibuprofen in our drug database, searched medical sources for evidence, and then formatted everything in a way that's easy to understand!
```

---

## 🚀 Explaining to a Hackathon Crowd

### The Elevator Pitch

"PharmaMiku is a **Glass Box AI Agent** - meaning you can see exactly how it thinks. When you ask a question, 6 specialized AI agents work together: one classifies your question, one checks safety, one looks up medical evidence, one makes it user-friendly, one double-checks everything, and one explains how it all worked. Every step is logged and traceable, so you can see the reasoning behind every answer."

### The Technical Pitch

"We built a multi-agent system with complete observability. The orchestrator coordinates 6 specialized agents that process queries sequentially, with each agent's output feeding into the next. We use a dynamic tool system for extensibility, and every decision, tool call, and state change is logged to a trace file. The frontend visualizes these traces in real-time, and we analyze patterns across all executions to improve the system."

### Key Differentiators

1. **Complete Transparency** - Not a black box, every step is visible
2. **Multi-Agent Architecture** - Specialized agents vs. single monolithic model
3. **Dynamic Tools** - Extensible system for adding capabilities
4. **Real-time Observability** - See what's happening as it happens
5. **Safety-First** - Multiple safety checks throughout the pipeline

---

## 📚 Further Reading

- **Orchestrator Code:** `backend/agents/orchestrator.py`
- **Trace Manager:** `backend/observability/trace_manager.py`
- **Tool System:** `backend/tools/`
- **Frontend API:** `frontend/utils/api.ts`

---

**Built with ❤️ for The Great Agent Hack 2025**

