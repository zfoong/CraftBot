# -*- coding: utf-8 -*-
"""
Session routing prompts for agent_core.

This module contains prompt templates for routing messages to sessions.
"""

# --- Unified Session Routing ---
# This prompt is the LAST-RESORT routing decision. The chat handler short-circuits
# the easy cases deterministically (explicit UI reply target, third-party
# notifications, single waiting task, reply markers) BEFORE this prompt runs.
# By the time the LLM sees the message, those cases are already handled.
#
# The prompt's job: decide if a message in main chat with active task(s) is
# CLEARLY a continuation/modification of one of those tasks, or a new request.
# Default to NEW SESSION when in doubt.
ROUTE_TO_SESSION_PROMPT = """
<objective>
You are a session router. Decide whether an incoming message is a clear continuation
of an existing task, or a new request that should open a new session.
</objective>

<incoming_item>
Type: {item_type}
Content: {item_content}
Source Platform: {source_platform}
User's current Living UI page: {current_living_ui_id}
</incoming_item>

<existing_sessions>
{existing_sessions}
</existing_sessions>

<recent_conversation>
Recent messages across all sessions (oldest first, may include completed tasks
that are no longer in <existing_sessions>):
{recent_conversation}
</recent_conversation>

<rules>
DEFAULT: create a new session. When in doubt, choose "new".

Route to an existing session ONLY IF the message clearly fits ONE of these:
  - References a specific file, output, or artifact created by that task
    (e.g. "the PDF you made", "the translated report", a filename produced by that task)
  - Is a clear modification of that task's original instruction
    (e.g. "translate to Spanish instead", "also include X", "skip page 5", "make it shorter")
  - Cancels or pauses that task explicitly
    (e.g. "stop the translation", "pause the report", "cancel that task")
  - Is a context-dependent message ("fix this", "it's broken", "add a feature")
    AND there is an active task whose Living UI ID matches the user's current
    Living UI page (see <incoming_item> above)
  - Explicitly names a Living UI app/project that matches one of the active
    tasks' Living UI bindings — even if the user is currently viewing a
    different Living UI page. Chat is global; the user can talk about any
    Living UI from anywhere.

DO NOT route based on:
  - "There's only one active task" — single active task is NOT a reason to route
    a generic message to it. This bias previously caused multiple wrong-routing bugs.
  - Generic acknowledgments ("thanks", "ok", "got it", "yes", "no") — these are
    conversational. Create a new session.
  - Topic resemblance alone — "I want to translate something" while a translate
    task is running is a NEW request, not a modification of the active task,
    unless the user explicitly says so.
  - "[REPLYING TO PREVIOUS AGENT MESSAGE]:" markers — those are handled before
    this prompt runs and won't reach you.

Living UI specifics:
  - The user's current Living UI page is a CONTEXT hint, not a hard binding.
  - For context-dependent messages with no explicit reference, prefer the task
    bound to the user's current Living UI.
  - For messages that explicitly name a different Living UI (by app name, project
    path, or feature description that clearly belongs to that other Living UI),
    route to THAT Living UI's task instead.
  - If no active task matches the referenced Living UI, choose new session.

Using <recent_conversation>:
  - It tells you what was just discussed across the whole agent (not just one
    task). Use it to disambiguate context-dependent messages — e.g., "and
    Spanish" makes sense if the previous message was about translation.
  - If the recent conversation shows a task topic that has already COMPLETED
    (no longer in <existing_sessions>), prefer creating a new session over
    routing to an unrelated active task. The completed task can't be resumed.
  - If the recent conversation contains nothing relevant, treat the message
    purely on its own merits per the rules above.

The "agent asked a question, user is answering" case is handled
deterministically before this prompt runs (via the waiting_for_user_reply flag).
You do NOT need to consider it.
</rules>

<output_format>
Return ONLY a valid JSON object:
- Route to existing: {{ "reason": "<brief>", "action": "route", "session_id": "<session_id>" }}
- Create new: {{ "reason": "<brief>", "action": "new", "session_id": "new" }}
</output_format>
"""

__all__ = [
    "ROUTE_TO_SESSION_PROMPT",
]
