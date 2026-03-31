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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port={{BACKEND_PORT}})
