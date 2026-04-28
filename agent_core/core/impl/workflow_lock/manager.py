# -*- coding: utf-8 -*-
"""WorkflowLockManager — exclusive locks for named background workflows.

A *workflow* is any recurring background activity that must not run concurrently
with another instance of itself (e.g. memory processing, proactive cycles).
Each workflow is identified by a stable string. At most one task may own a
given workflow lock at a time.

Typical usage:

    if not await locks.try_acquire("memory_processing"):
        logger.info("workflow already active; skipping")
        return

    try:
        task_id = task_manager.create_task(..., workflow_id="memory_processing")
        # TaskManager auto-releases the lock in its _end_task funnel when the
        # task terminates (completed / error / cancelled).
    except Exception:
        # Release on any failure before the task takes ownership.
        await locks.release("memory_processing")
        raise

The manager is safe for concurrent callers inside a single asyncio event loop
because every mutation is guarded by an internal ``asyncio.Lock``.
"""

from __future__ import annotations

import asyncio
from typing import FrozenSet, Set


class WorkflowLockManager:
    """Registry of exclusive locks for named background workflows."""

    def __init__(self) -> None:
        self._held: Set[str] = set()
        self._mutex = asyncio.Lock()

    async def try_acquire(self, workflow_id: str) -> bool:
        """Attempt to acquire the lock for ``workflow_id``.

        Returns True on success, False if another holder already owns it.
        """
        if not workflow_id:
            raise ValueError("workflow_id must be a non-empty string")
        async with self._mutex:
            if workflow_id in self._held:
                return False
            self._held.add(workflow_id)
            return True

    async def release(self, workflow_id: str) -> None:
        """Release the lock for ``workflow_id``. Idempotent."""
        if not workflow_id:
            return
        async with self._mutex:
            self._held.discard(workflow_id)

    def is_locked(self, workflow_id: str) -> bool:
        """Non-blocking check — True iff a holder currently owns ``workflow_id``."""
        return workflow_id in self._held

    def active_workflows(self) -> FrozenSet[str]:
        """Snapshot of all currently-held workflow ids."""
        return frozenset(self._held)
