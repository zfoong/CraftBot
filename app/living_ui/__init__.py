"""Living UI module for managing dynamic agent-aware user interfaces."""

from typing import Optional, Callable, Awaitable
from .manager import LivingUIManager, LivingUIProject

__all__ = [
    'LivingUIManager',
    'LivingUIProject',
    'get_living_ui_manager',
    'set_living_ui_manager',
    'register_broadcast_callbacks',
    'broadcast_living_ui_ready',
    'broadcast_living_ui_progress',
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


async def broadcast_living_ui_ready(project_id: str, url: str, port: int) -> bool:
    """
    Broadcast that a Living UI is ready.

    This can be called from actions to notify the browser.

    Returns:
        True if project was found and launched successfully, False otherwise
    """
    if _broadcast_ready_callback:
        return await _broadcast_ready_callback(project_id, url, port)
    return False


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
