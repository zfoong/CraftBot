# -*- coding: utf-8 -*-
"""Workflow lock registry — prevents overlapping execution of named workflows."""

from agent_core.core.impl.workflow_lock.manager import WorkflowLockManager

__all__ = ["WorkflowLockManager"]
