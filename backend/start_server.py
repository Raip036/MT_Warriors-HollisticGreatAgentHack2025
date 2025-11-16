#!/usr/bin/env python3
"""
Optimized server startup script for PharmaMiku backend.
Uses Uvicorn with multiple workers for better concurrency.
"""

import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Get the directory of this script
    BASE_DIR = Path(__file__).resolve().parent
    
    # Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    WORKERS = int(os.getenv("WORKERS", 4))  # Number of worker processes
    RELOAD = os.getenv("RELOAD", "false").lower() == "true"  # Auto-reload for development
    
    print(f"🚀 Starting PharmaMiku backend server...")
    print(f"   Host: {HOST}")
    print(f"   Port: {PORT}")
    print(f"   Workers: {WORKERS}")
    print(f"   Reload: {RELOAD}")
    
    uvicorn.run(
        "server:app",
        host=HOST,
        port=PORT,
        workers=WORKERS if not RELOAD else 1,  # Workers don't work with reload
        reload=RELOAD,
        log_level="info",
        access_log=True,
        # Performance optimizations
        loop="asyncio",
        http="httptools",  # Faster HTTP parsing
        ws="websockets",  # WebSocket support
        # Connection limits
        limit_concurrency=100,
        limit_max_requests=1000,
        timeout_keep_alive=5,
    )

