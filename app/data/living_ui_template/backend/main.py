"""
Living UI Python Backend

FastAPI backend for Living UI projects.
Provides REST API for state management and data persistence.

To run manually:
    uvicorn main:app --port {{BACKEND_PORT}} --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from routes import router
from database import init_db
from logger import setup_logging, cleanup_old_logs
import logging

# Initialize persistent file-based logging before anything else
setup_logging()
cleanup_old_logs(keep=20)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup, start health checker."""
    from health_checker import start_health_checker, stop_health_checker

    logger.info("[Backend] Initializing database...")
    await init_db()
    logger.info("[Backend] Database initialized")
    start_health_checker(port={{BACKEND_PORT}})
    logger.info("[Backend] Health checker started")
    yield
    stop_health_checker()
    logger.info("[Backend] Shutting down...")


app = FastAPI(
    title="{{PROJECT_NAME}} API",
    description="Backend API for {{PROJECT_NAME}} Living UI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint for process management."""
    return {"status": "healthy", "project": "{{PROJECT_ID}}"}


# ============================================================================
# Frontend Console Log Capture (registered on app directly, not on router,
# so it survives agent rewrites of routes.py)
# ============================================================================
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from datetime import datetime

_FRONTEND_LOG_PATH = Path(__file__).parent / "logs" / "frontend_console.log"


class _FrontendLogEntry(BaseModel):
    level: str
    message: str
    timestamp: Optional[str] = None


class _FrontendLogBatch(BaseModel):
    entries: List[_FrontendLogEntry]


@app.post("/api/logs")
async def capture_frontend_logs(data: _FrontendLogBatch):
    """Capture frontend console logs for agent debugging."""
    _FRONTEND_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_FRONTEND_LOG_PATH, "a", encoding="utf-8") as f:
        for entry in data.entries:
            ts = entry.timestamp or datetime.utcnow().isoformat()
            f.write(f"{ts} | {entry.level.upper():<5} | {entry.message}\n")
    return {"status": "ok", "count": len(data.entries)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port={{BACKEND_PORT}})
