# -*- coding: utf-8 -*-
"""
Session routing prompts for agent_core.

This module contains prompt templates for routing messages to sessions.
"""

# --- Unified Session Routing ---
# This prompt handles BOTH incoming messages AND triggers in a single LLM call.
# Provides rich context including task details, progress, and platform info.
ROUTE_TO_SESSION_PROMPT = """
<objective>
You are a session routing system. Determine which task session an incoming message belongs to.
</objective>

<incoming_item>
Type: {item_type}
Content: {item_content}
Source Platform: {source_platform}
</incoming_item>

<existing_sessions>
{existing_sessions}
</existing_sessions>

<recent_conversation>
{recent_conversation}
</recent_conversation>

<rules>
1. ROUTE TO EXISTING SESSION when:
   - The message is a response to a question the agent asked (check Recent Activity)
   - Short replies like "yes", "no", "ok", numbers → route to related session waiting for reply
   - The message is related to an existing task's topic or instruction
   - The message references files, outputs, or artifacts created by an existing task (check Recent Activity for file paths)

2. SINGLE ACTIVE SESSION BIAS:
   - When there is ONLY ONE active session, strongly prefer routing to it unless the message is clearly about a completely different topic
   - This is because follow-up requests often relate to the current task's outputs (e.g., "convert to PDF" after a report was generated)

3. CREATE NEW SESSION when:
   - The message is a NEW topic clearly unrelated to any existing task
   - The message doesn't match any existing task's context AND there are multiple active sessions
   - The message appears to be a follow-up to a COMPLETED task visible in recent conversation history but NOT in existing sessions

IMPORTANT NOTES:
- If the message has no context, it is very LIKELY it is meant for another task, DO NOT CREATE a new session
- If there is on-going task waiting for user reply, it is very LIKELY the incoming item is meant for the session
- However, if recent conversation history shows a completed task matching the message topic, prefer creating a new session over routing to an unrelated active task
- When the incoming message is ambiguous and could match any session, slightly prefer the most recent conversation topic (latest messages in recent conversation history)
- People naturally respond to the most recent thing discussed, so an out-of-context reply like "is it good?" most likely refers to the latest topic, not an older one
</rules>

<output_format>
Return ONLY a valid JSON object:
- Route to existing: {{ "action": "route", "session_id": "<session_id>", "reason": "<brief>" }}
- Create new: {{ "action": "new", "session_id": "new", "reason": "<brief>" }}
</output_format>
"""

__all__ = [
    "ROUTE_TO_SESSION_PROMPT",
]
