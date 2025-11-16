from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio

from agents.orchestrator import Orchestrator

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
    progress_queue = queue.Queue()
    
    def progress_callback(stage: str, message: str):
        progress_queue.put({"type": "progress", "stage": stage, "message": message})
    
    async def generate():
        import threading
        
        # Start orchestrator in a thread
        result = {"final": None, "trace": None, "error": None}
        
        def run_orchestrator():
            try:
                final, trace = orch.run_with_progress(req.message, progress_callback)
                result["final"] = final
                result["trace"] = trace
            except Exception as e:
                result["error"] = str(e)
        
        thread = threading.Thread(target=run_orchestrator)
        thread.start()
        
        # Stream progress updates
        while thread.is_alive():
            try:
                update = progress_queue.get(timeout=0.1)
                yield f"data: {json.dumps(update)}\n\n"
            except queue.Empty:
                await asyncio.sleep(0.1)
                continue
        
        thread.join()
        
        # Send final result
        if result["error"]:
            yield f"data: {json.dumps({'type': 'error', 'error': result['error']})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'complete', 'response': result['final'], 'citations': result['trace'].get('citations', []), 'trace': result['trace']})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# -----------------------------
# ROOT ENDPOINT
# -----------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "PharmaMiku backend running"}
