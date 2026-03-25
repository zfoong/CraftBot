# -*- coding: utf-8 -*-
"""Global runtime state for a single-user, single-agent process."""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from app.state.types import AgentProperties
from app.task import Task

@dataclass
class AgentState:
    """Authoritative runtime state for the agent."""

    current_task: Optional[Task] = None
    event_stream: Optional[str] = None
    gui_mode: bool = False
    agent_properties: AgentProperties = AgentProperties(current_task_id="", action_count=0)

    # Living UI state tracking
    _living_ui_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _active_living_ui_id: Optional[str] = None

    def update_current_task(self, new_task: Optional[Task]) -> None:
        self.current_task = new_task

    def update_event_stream(self, new_event_stream: Optional[str]) -> None:
        self.event_stream = new_event_stream

    def update_gui_mode(self, gui_mode: bool) -> None:
        self.gui_mode = gui_mode

    def refresh(
        self,
        *,
        current_task: Optional[Task] = None,
        event_stream: Optional[str] = None,
        gui_mode: Optional[bool] = None,
    ) -> None:
        """Update only fields that changed."""
        self.current_task = current_task
        self.event_stream = event_stream
        self.gui_mode = gui_mode

    def set_agent_property(self, key, value):
        """
        Sets a global agent property (not specific to any task).
        """
        self.agent_properties.set_property(key, value)

    def get_agent_property(self, key, default=None):
        """
        Retrieves a global agent property.
        """
        return self.agent_properties.get_property(key, default)

    def get_agent_properties(self):
        """
        Retrieves all global agent properties.
        """
        return self.agent_properties.to_dict()

    # -------------------------------------------------------------------------
    # Living UI State Methods
    # -------------------------------------------------------------------------

    def update_living_ui_state(self, project_id: str, state: Dict[str, Any]) -> None:
        """
        Store the latest state from a Living UI.

        Args:
            project_id: The Living UI project ID
            state: The UI state snapshot from the Living UI
        """
        self._living_ui_states[project_id] = {
            **state,
            "received_at": time.time(),
        }

    def get_living_ui_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a Living UI.

        Args:
            project_id: The Living UI project ID

        Returns:
            The UI state or None if not found
        """
        return self._living_ui_states.get(project_id)

    def set_active_living_ui(self, project_id: Optional[str]) -> None:
        """Set the currently active Living UI (the one user is viewing)."""
        self._active_living_ui_id = project_id

    def get_active_living_ui(self) -> Optional[str]:
        """Get the currently active Living UI ID."""
        return self._active_living_ui_id

    def get_living_ui_context(self) -> str:
        """
        Generate context string for LLM about active Living UIs.

        Returns:
            Formatted string describing the current state of active Living UIs
        """
        if not self._living_ui_states:
            return ""

        context_parts = ["## Active Living UIs\n"]

        for project_id, state in self._living_ui_states.items():
            is_active = project_id == self._active_living_ui_id
            active_marker = " (USER IS VIEWING)" if is_active else ""

            context_parts.append(f"### Living UI: {project_id}{active_marker}")

            # Current view
            current_view = state.get("currentView", "unknown")
            context_parts.append(f"- Current View: {current_view}")

            # Visible text (truncated)
            visible_text = state.get("visibleText", [])
            if visible_text:
                text_preview = " | ".join(visible_text[:10])
                if len(text_preview) > 200:
                    text_preview = text_preview[:200] + "..."
                context_parts.append(f"- Visible Text: {text_preview}")

            # User inputs
            input_values = state.get("inputValues", {})
            if input_values:
                context_parts.append(f"- User Inputs: {json.dumps(input_values)}")

            # Component states
            component_tree = state.get("componentTree", [])
            if component_tree:
                components = [c.get("name", "unknown") for c in component_tree]
                context_parts.append(f"- Components: {', '.join(components)}")

            context_parts.append("")

        return "\n".join(context_parts)

    def clear_living_ui_state(self, project_id: str) -> None:
        """Clear state for a Living UI (e.g., when stopped or deleted)."""
        if project_id in self._living_ui_states:
            del self._living_ui_states[project_id]
        if self._active_living_ui_id == project_id:
            self._active_living_ui_id = None

# ---- Global runtime state ----
STATE = AgentState()
