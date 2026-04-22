# Task sessions

A **task session** is the unit of work inside CraftBot. Every ask — "schedule a meeting", "find me a flight", "review my PR" — becomes a task, with its own id, todos, [event stream](event-stream.md), temp workspace, and [triggers](trigger.md) pointing at it.

## Beginner mental model

A task is a dataclass with three jobs:

- **Identity** — a unique `id` that all triggers, events, and streams for this work reference.
- **Progress** — a list of `todos` (simple checkboxes) so the agent (and you) can see what's done and what's next.
- **Scope** — an `action_sets` list that limits which [actions](action.md) the agent can call, plus a `selected_skills` list that injects domain instructions into its prompt.

Tasks sleep and resume. A task can pause waiting for a user reply, resume 3 hours later, and continue where it left off — the `id` keeps the stream and todos intact.

## Inspect it now

Use the `/menu` command (in TUI or browser) to see active sessions, or tail logs:

```bash
tail -f logs/*.log | grep -E "\[TASK|task_id|session_id"
```

## Example task

```json
{
  "id": "4f2c1a9b-...",
  "name": "Research Q2 earnings",
  "instruction": "Summarize our Q2 earnings, compare to Q1, DM Bob the summary",
  "mode": "complex",
  "status": "running",
  "todos": [
    {"content": "Fetch Q2 earnings report", "status": "completed"},
    {"content": "Fetch Q1 earnings for comparison", "status": "in_progress"},
    {"content": "Draft summary with key deltas", "status": "pending"},
    {"content": "DM Bob on Slack", "status": "pending"}
  ],
  "action_sets": ["file_operations", "web_research"],
  "selected_skills": ["financial-analyst"],
  "waiting_for_user_reply": false,
  "source_platform": "CraftBot Interface"
}
```

## Lifecycle

```
created  →  running  ⇄  paused     →  completed
                    ↘
                     waiting_for_user_reply
                    ↙
                 error | cancelled
```

Status transitions happen through the [agent loop](agent-loop.md). `waiting_for_user_reply` is special: it keeps the task `running` but suspends trigger scheduling until the user replies (a fresh trigger with `fire_at=now` re-wakes it via [`fire()`](trigger.md#the-queue-put-get-fire)).

## Fields

| Field | Purpose |
|---|---|
| `id` | Session id — shared by triggers, events, and streams |
| `name` / `instruction` | Human-readable label + the original user ask |
| `mode` | `"simple"` or `"complex"` — drives which [mode workflow](../modes/index.md) handles it |
| `status` | `running` / `completed` / `error` / `paused` / `cancelled` |
| `todos` | [TodoItem] — content, status (`pending` / `in_progress` / `completed`), active form, uuid |
| `action_sets` | Whitelist of action set names (`file_operations`, `web_research`, etc.) |
| `compiled_actions` | Cached flat list of action names compiled from the sets |
| `selected_skills` | Skills whose instructions inject into the prompt |
| `temp_dir` | Per-task scratch directory (outputs too large for the event stream live here) |
| `waiting_for_user_reply` | Pauses trigger scheduling until `fire()` |
| `source_platform` | Where outbound messages go — `"Slack"`, `"Telegram"`, or `"CraftBot Interface"` |
| `final_summary` | Populated at task end; becomes the observable outcome |

## Action sets (scoping)

Action sets limit what a task can do. Default sets:

| Set | Contains |
|---|---|
| `core` | Always included — `send_message`, task management, set management |
| `file_operations` | File I/O — read, write, search, edit |
| `web_research` | Web search, fetch URLs |
| `document_processing` | PDF and office document handling |
| `clipboard` | Clipboard read/write |
| `shell` | `run_shell` and Python exec |
| `gui_interaction` | Mouse, keyboard, screen (only if GUI mode is on) |

Action sets are chosen by the LLM when the task is created (via `task_start` action). You can also force a set with a directive when starting a task.

## Multi-tasking

Multiple tasks can run concurrently. Each one gets its own event stream via `on_stream_create(task_id, temp_dir)` — critical to prevent event leakage between sessions. The [trigger queue](trigger.md) uses `session_id` to keep triggers scoped to their owning task.

## Persistence & recovery

Tasks are persisted to disk on every change via `on_task_persist` / `on_task_remove_persist` hooks, so a crash doesn't lose them. On restart, running tasks are rehydrated and their triggers re-queued.

## Simple vs. complex

- **Simple** — streamlined, no visible todos, runs to completion after delivering a result. Best for "send X", "look up Y". See [Simple task](../modes/simple-task.md).
- **Complex** — full todo loop with planning. Best for multi-step work. See [Complex task](../modes/complex-task.md).

The LLM picks the mode when creating the task, based on the user instruction and examples from the prompt.

## Related

- [Agent loop](agent-loop.md) — how tasks are executed
- [Triggers](trigger.md) — how tasks are woken up
- [Event stream](event-stream.md) — the per-task narrative
- [Task modes](../modes/index.md) — simple vs complex vs GUI vs proactive
- [Actions catalogue](../reference/actions.md) — action sets and their contents
