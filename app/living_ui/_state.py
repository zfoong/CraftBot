"""Module-level singleton for the LivingUIManager.

Lives in its own file so that `broadcast.py` and `actions.py` can import the
accessor without triggering circular imports through `__init__.py`.
"""

from typing import Optional

from .manager import LivingUIManager

_manager: Optional[LivingUIManager] = None


def get_living_ui_manager() -> Optional[LivingUIManager]:
    """Get the global LivingUIManager instance."""
    return _manager


def set_living_ui_manager(manager: LivingUIManager) -> None:
    """Set the global LivingUIManager instance (called by browser_adapter)."""
    global _manager
    _manager = manager
