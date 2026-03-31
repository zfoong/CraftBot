"""Living UI module for managing dynamic agent-aware user interfaces."""

from typing import Optional, Callable, Awaitable

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from .manager import LivingUIManager, LivingUIProject

__all__ = [
    'LivingUIManager',
    'LivingUIProject',
    'get_living_ui_manager',
    'set_living_ui_manager',
    'register_broadcast_callbacks',
    'broadcast_living_ui_ready',
    'broadcast_living_ui_progress',
    'restart_living_ui',
]

# Module-level singleton for global access
_manager: Optional[LivingUIManager] = None

# Callbacks for broadcasting to browser (set by browser_adapter)
# broadcast_ready returns True if project was found and launched successfully, False otherwise
_broadcast_ready_callback: Optional[Callable[[str, str, int], Awaitable[bool]]] = None
_broadcast_progress_callback: Optional[Callable[[str, str, int, str], Awaitable[None]]] = None


def get_living_ui_manager() -> Optional[LivingUIManager]:
    """Get the global LivingUIManager instance."""
    return _manager


def set_living_ui_manager(manager: LivingUIManager) -> None:
    """Set the global LivingUIManager instance (called by browser_adapter)."""
    global _manager
    _manager = manager


def register_broadcast_callbacks(
    broadcast_ready: Callable[[str, str, int], Awaitable[bool]],
    broadcast_progress: Callable[[str, str, int, str], Awaitable[None]],
) -> None:
    """
    Register broadcast callbacks for Living UI actions to use.

    This is called by the browser_adapter when it initializes.

    Args:
        broadcast_ready: Async function to broadcast that a Living UI is ready
        broadcast_progress: Async function to broadcast progress updates
    """
    global _broadcast_ready_callback, _broadcast_progress_callback
    _broadcast_ready_callback = broadcast_ready
    _broadcast_progress_callback = broadcast_progress
    logger.info("[LIVING_UI] Broadcast callbacks registered")


async def broadcast_living_ui_ready(project_id: str, url: str, port: int) -> bool:
    """
    Broadcast that a Living UI is ready.

    This can be called from actions to notify the browser.

    Returns:
        True if project was found and launched successfully, False otherwise
    """
    if _broadcast_ready_callback:
        return await _broadcast_ready_callback(project_id, url, port)
    logger.warning(f"[LIVING_UI] broadcast_living_ui_ready called but callback is None (manager={_manager is not None})")
    return False


async def restart_living_ui(project_id: str) -> dict:
    """
    Restart a running Living UI project (backend + frontend).

    Stops the entire project and relaunches via the pipeline.
    Returns detailed errors if any step fails.

    Args:
        project_id: The Living UI project ID

    Returns:
        Dict with status, message, url/backend_url on success, or errors on failure.
    """
    if not _manager:
        return {"status": "error", "message": "Living UI manager not initialized"}

    project = _manager.get_project(project_id)
    if not project:
        return {"status": "error", "message": f"Project '{project_id}' not found"}

    # Stop the entire project (backend + frontend)
    await _manager.stop_project(project_id)

    # Relaunch via the full pipeline
    result = await _manager.launch_and_verify(project_id)

    if result["status"] == "success":
        return {
            "status": "success",
            "message": f"Living UI '{project_id}' restarted",
            "url": result.get("url"),
            "backend_url": result.get("backend_url"),
        }
    else:
        errors = result.get("errors", [])
        errors_str = "\n".join(errors[:10])
        return {
            "status": "error",
            "message": f"Restart failed at step: {result.get('step', 'unknown')}",
            "test_errors": errors[:10],
            "details": f"Fix these errors and call living_ui_restart again:\n{errors_str}",
        }


async def broadcast_living_ui_progress(
    project_id: str, phase: str, progress: int, message: str
) -> bool:
    """
    Broadcast Living UI creation progress.

    Returns:
        True if broadcast was successful, False otherwise
    """
    if _broadcast_progress_callback:
        await _broadcast_progress_callback(project_id, phase, progress, message)
        return True
    return False
