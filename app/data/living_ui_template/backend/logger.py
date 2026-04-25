"""
Living UI Backend Logger

Persistent file-based logging for Living UI backend.
Logs are written to the project's logs/ directory with automatic rotation.
Each session (server start) creates a new log file, old logs are retained.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Log directory lives inside the project's backend folder
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging() -> logging.Logger:
    """
    Configure persistent file-based logging for the backend.

    Creates a timestamped log file per session so each server run
    is independently traceable. Also logs to stderr for subprocess capture.

    Returns:
        The root logger, configured with file + stream handlers.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"backend_{timestamp}.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler - captures everything (DEBUG+)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Stream handler - INFO+ to stderr (captured by manager subprocess pipes)
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    # Also capture uvicorn logs into the same file
    for uvi_logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uvi_logger = logging.getLogger(uvi_logger_name)
        uvi_logger.handlers = []  # Remove default handlers
        uvi_logger.addHandler(file_handler)
        uvi_logger.addHandler(stream_handler)
        uvi_logger.propagate = False

    root_logger.info(f"[Logger] Session log started: {log_file}")
    root_logger.info(f"[Logger] Python {sys.version}")
    root_logger.info(f"[Logger] CWD: {os.getcwd()}")

    return root_logger


def cleanup_old_logs(keep: int = 20):
    """Remove old log files, keeping the most recent `keep` files."""
    log_files = sorted(LOG_DIR.glob("backend_*.log"), reverse=True)
    for old_log in log_files[keep:]:
        try:
            old_log.unlink()
        except Exception:
            pass
