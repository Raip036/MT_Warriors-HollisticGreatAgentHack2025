from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import uuid
from typing import Any

from agents.orchestrator import Orchestrator
from observability import get_trace_manager, generate_step_summary, TraceAnalyzer
from utils.cache import get_cached_response, set_cached_response
import httpx


def safe_json_serialize(obj: Any) -> str:
    """
    Safely serialize an object to JSON, handling circular references
    and non-serializable objects.
    """
    def default_serializer(o):
        if isinstance(o, (set, frozenset)):
            return list(o)
        if hasattr(o, '__dict__'):
            try:
                return o.__dict__
            except:
                return str(o)
        return str(o)
    
    try:
        return json.dumps(obj, default=default_serializer, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        # If serialization fails, try to clean the object
        cleaned = clean_for_serialization(obj)
        return json.dumps(cleaned, default=default_serializer, ensure_ascii=False)


def clean_for_serialization(obj: Any, seen: set = None, max_depth: int = 50) -> Any:
    """
    Recursively clean an object to remove circular references
    and ensure it's JSON serializable.
    
    Args:
        obj: Object to clean
        seen: Set of object IDs already seen (to detect cycles)
        max_depth: Maximum recursion depth to prevent stack overflow
    """
    if seen is None:
        seen = set()
    
    # Prevent infinite recursion
    if max_depth <= 0:
        return "<max depth exceeded>"
    
    # Handle None
    if obj is None:
        return None
    
    # Handle primitive types
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    # Check for circular references
    try:
        obj_id = id(obj)
        if obj_id in seen:
            return "<circular reference>"
    except TypeError:
        # Some objects can't be hashed (like dicts in some cases)
        # Use a different approach
        pass
    
    # Handle dict
    if isinstance(obj, dict):
        try:
            obj_id = id(obj)
            if obj_id in seen:
                return "<circular reference>"
            seen.add(obj_id)
        except TypeError:
            pass
        
        result = {}
        for key, value in obj.items():
            # Skip structured_trace to avoid circular references
            if key == "structured_trace":
                continue
            try:
                # Ensure key is JSON-serializable
                if isinstance(key, (str, int, float, bool)):
                    clean_key = key
                else:
                    clean_key = str(key)
                result[clean_key] = clean_for_serialization(value, seen, max_depth - 1)
            except Exception as e:
                result[str(key)] = f"<serialization error: {str(e)}>"
        
        try:
            seen.discard(obj_id)
        except (NameError, TypeError):
            pass
        return result
    
    # Handle list/tuple
    elif isinstance(obj, (list, tuple)):
        try:
            obj_id = id(obj)
            if obj_id in seen:
                return "<circular reference>"
            seen.add(obj_id)
        except TypeError:
            pass
        
        result = [clean_for_serialization(item, seen, max_depth - 1) for item in obj]
        
        try:
            seen.discard(obj_id)
        except (NameError, TypeError):
            pass
        return result
    
    # Handle Pydantic models and other objects with __dict__
    elif hasattr(obj, '__dict__'):
        try:
            obj_id = id(obj)
            if obj_id in seen:
                return "<circular reference>"
            seen.add(obj_id)
        except TypeError:
            pass
        
        try:
            # Try to get dict representation
            if hasattr(obj, 'model_dump'):
                # Pydantic model
                result = clean_for_serialization(obj.model_dump(), seen, max_depth - 1)
            elif hasattr(obj, 'dict'):
                # Pydantic v1
                result = clean_for_serialization(obj.dict(), seen, max_depth - 1)
            else:
                result = clean_for_serialization(obj.__dict__, seen, max_depth - 1)
        except Exception as e:
            result = f"<object serialization error: {str(e)}>"
        
        try:
            seen.discard(obj_id)
        except (NameError, TypeError):
            pass
        return result
    
    # Handle datetime and other common types
    elif hasattr(obj, 'isoformat'):
        # datetime objects
        return obj.isoformat()
    
    # Fallback: convert to string
    else:
        try:
            return str(obj)
        except Exception:
            return "<unserializable object>"

# -----------------------------
# FASTAPI SETUP
# -----------------------------
app = FastAPI()

# Allow frontend (Next.js) to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # you can restrict later
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# INITIALISE ORCHESTRATOR
# -----------------------------
orch = Orchestrator()

# -----------------------------
# HTTP CLIENT WITH CONNECTION POOLING
# -----------------------------
http_client = httpx.AsyncClient(
    timeout=60.0,
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
)

# -----------------------------
# REQUEST MODEL
# -----------------------------
class AskRequest(BaseModel):
    message: str

# -----------------------------
# ENDPOINT: /ask (with SSE progress updates)
# -----------------------------
@app.post("/ask")
async def ask_backend(req: AskRequest):
    import queue
    from concurrent.futures import ThreadPoolExecutor
    
    # Check cache first
    cached = get_cached_response(req.message)
    if cached:
        session_id = str(uuid.uuid4())
        
        async def generate_cached():
            yield f"data: {json.dumps({'type': 'progress', 'stage': 'cached', 'message': 'Retrieving cached response...'})}\n\n"
            await asyncio.sleep(0.1)  # Small delay for UX
            
            response_data = {
                'type': 'complete',
                'response': cached.get('response', ''),
                'citations': cached.get('citations', []),
                'trace': cached.get('trace', {}),
                'session_id': session_id,
                'cached': True
            }
            yield f"data: {safe_json_serialize(response_data)}\n\n"
        
        return StreamingResponse(generate_cached(), media_type="text/event-stream")
    
    progress_queue = queue.Queue()
    
    # Generate session ID for this request
    session_id = str(uuid.uuid4())
    
    def progress_callback(stage: str, message: str):
        progress_queue.put({"type": "progress", "stage": stage, "message": message})
    
    async def generate():
        # Use ThreadPoolExecutor for better async integration
        loop = asyncio.get_event_loop()
        executor = ThreadPoolExecutor(max_workers=1)
        
        result = {"final": None, "trace": None, "error": None, "session_id": session_id}
        
        def run_orchestrator():
            try:
                final, trace = orch.run_with_progress(req.message, progress_callback, session_id=session_id)
                result["final"] = final
                result["trace"] = trace
            except Exception as e:
                result["error"] = str(e)
        
        # Run orchestrator in thread pool
        future = loop.run_in_executor(executor, run_orchestrator)
        
        # Stream progress updates while waiting
        while not future.done():
            try:
                update = progress_queue.get(timeout=0.1)
                yield f"data: {json.dumps(update)}\n\n"
            except queue.Empty:
                await asyncio.sleep(0.05)  # Reduced sleep for faster updates
                continue
        
        # Wait for completion
        await future
        
        # Send final result
        if result["error"]:
            yield f"data: {json.dumps({'type': 'error', 'error': result['error'], 'session_id': session_id})}\n\n"
        else:
            # Clean trace to remove circular references and structured_trace
            trace = result['trace']
            if trace:
                # Remove structured_trace as it's redundant (can be fetched via /trace/{session_id})
                trace_clean = {k: v for k, v in trace.items() if k != 'structured_trace'}
                # Clean for any other potential circular references
                trace_clean = clean_for_serialization(trace_clean)
            else:
                trace_clean = {}
            
            response_data = {
                'type': 'complete',
                'response': result['final'],
                'citations': trace.get('citations', []) if trace else [],
                'trace': trace_clean,
                'session_id': session_id
            }
            
            # Cache the response
            set_cached_response(
                req.message,
                {
                    'response': result['final'],
                    'citations': trace.get('citations', []) if trace else [],
                    'trace': trace_clean
                }
            )
            
            yield f"data: {safe_json_serialize(response_data)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# -----------------------------
# TRACE ENDPOINT
# -----------------------------
@app.get("/trace/{session_id}")
async def get_trace(session_id: str):
    """
    Retrieve the full trace for a given session ID.
    Returns the structured trace with all steps, decisions, and tool calls.
    """
    trace_manager = get_trace_manager()
    trace = trace_manager.get_trace(session_id)
    
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace not found for session_id: {session_id}")
    
    # Add summaries to each step if not present
    for step in trace.get("steps", []):
        if "metadata" not in step:
            step["metadata"] = {}
        if "summary" not in step["metadata"]:
            step["metadata"]["summary"] = generate_step_summary(step)
    
    # Clean and serialize the trace to avoid recursion errors
    # Use our custom serialization function instead of FastAPI's jsonable_encoder
    cleaned_trace = clean_for_serialization(trace)
    
    # Return as JSONResponse with manually serialized data
    return JSONResponse(content=cleaned_trace)

# -----------------------------
# INSIGHTS ENDPOINT
# -----------------------------
@app.get("/insights")
async def get_insights(format: str = "json"):
    """
    Get behavioral insights from all traces.
    
    Args:
        format: Output format - "json" (default) or "report" for human-readable text
    
    Returns:
        JSON insights or plain text report
    """
    analyzer = TraceAnalyzer()
    insights = analyzer.analyze_all_traces()
    
    if format == "report":
        from fastapi.responses import PlainTextResponse
        report = analyzer.generate_report(insights)
        return PlainTextResponse(content=report)
    
    return insights

@app.get("/insights/csv")
async def get_insights_csv():
    """
    Export insights as CSV files for dashboard integration.
    Returns download links or file paths.
    """
    from pathlib import Path
    import tempfile
    
    analyzer = TraceAnalyzer()
    insights = analyzer.analyze_all_traces()
    
    # Create temporary directory for CSV files
    temp_dir = Path(tempfile.mkdtemp())
    csv_path = temp_dir / "insights"
    
    analyzer.export_to_csv(insights, csv_path)
    
    # Return paths to generated CSV files
    return {
        "tool_metrics_csv": str(csv_path.parent / f"{csv_path.stem}_tools.csv"),
        "step_metrics_csv": str(csv_path.parent / f"{csv_path.stem}_steps.csv"),
        "note": "CSV files generated. In production, consider serving these files directly or uploading to cloud storage."
    }

# -----------------------------
# ROOT ENDPOINT
# -----------------------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "PharmaMiku backend running"}

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await http_client.aclose()
