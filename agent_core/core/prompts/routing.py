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
Conversation ID: {conversation_id}
</incoming_item>

<existing_sessions>
{existing_sessions}
</existing_sessions>

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

IMPORTANT NOTES: 
- If the message has no context, it is very LIKELY it is meant for another task, DO NOT CREATE a new session
- If there is on-going task waiting for user reply, it is very LIKELY the incoming item is meant for the session
</rules>

<output_format>
Return ONLY a valid JSON object:
- Route to existing: {{ "action": "route", "session_id": "<session_id>", "reason": "<brief>" }}
- Create new: {{ "action": "new", "session_id": "new", "reason": "<brief>" }}
</output_format>
"""

# --- Action Input Resolution ---
RESOLVE_ACTION_INPUT_PROMPT = """
<objective>
You are responsible for providing input values to execute the following action:
- Action name: {name}
- Action type: {action_type}
- Action instruction: {description}
- Action code: {code}
- Current platform: {platform}
</objective>

<context>
Below is the schema of the required parameters for this action, please propose concrete values for these parameters:
{param_details_text}

You have to provide the input values based on the context provided below:
{context}
</context>

<event_stream>
This is the event stream of this task (from older to latest event):
{event_stream}
</event_stream>

<rules>
1. Return your answer in JSON format. For example, if the action requires parameters a and b,
   you might respond with something like: {{ "a": 42, "b": 7 }}.
2. For parameters with type "integer", ensure you provide an integer value.
3. For parameters with type "string", provide a short textual string.
4. Use the 'example' field as a guide if no other context is available.
5. Keep responses brief if the type is "string".
6. If you lack specific contextual clues, use your best guess from the provided example.
7. If a task has failed multiple times or encounter error that cannot be solved, you have to give up trying and inform user the action is impossible. If you do not give up, you will keep executing actions and causing infinite loop, which is very harmful.
8. When providing a boolean value, you must use "True" or "False", you cannot use lowercase "true" or "false".
9. You must provide all parameter values, otherwise 'parameter value not provided' error will occur.
</rules>

<objective>
- Only output JSON with the parameter names and values.
- You MUST follow the action instruction when contructing the action parameters.
- For instance: {{ "paramA": 123, "paramB": "some text" }}
</objective>
"""

__all__ = [
    "ROUTE_TO_SESSION_PROMPT",
    "RESOLVE_ACTION_INPUT_PROMPT",
]
