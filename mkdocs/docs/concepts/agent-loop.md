# Agent loop

The agent loop is the cycle CraftBot runs every time something wakes it up: **trigger → route → select action → execute → observe**.

## Beginner mental model

Think of the loop in three parts:

- **The doorbell** — a [trigger](trigger.md) fires (user message, schedule, external event, waiting-for-reply timeout).
- **The dispatcher** — CraftBot decides which of five *workflows* handles this trigger: memory, proactive, GUI task, complex task, simple task, or conversation.
- **The worker** — inside each workflow, a three-step beat: pick an [action](action.md), execute it, record what happened onto the [event stream](event-stream.md). Repeat until the trigger is done.

The agent does not run continuously. It sleeps until a trigger fires, then runs exactly one iteration of the loop. Long-running work happens by scheduling follow-up triggers.

## Inspect it now

Tail your logs and send a message. You'll see the loop's routing decisions:

```bash
tail -f logs/*.log | grep -E "\[REACT\]|\[WORKFLOW"
```

## Example output

```text
[REACT] starting...
[STATE] session_id=None | current_task_id=None | current_task=None
[WORKFLOW: CONVERSATION] Query: what's the weather in Tokyo
```

For a proactive heartbeat firing at midnight:

```text
[PROACTIVE] Trigger fired: type=proactive_heartbeat, frequency=daily, scope=
[PROACTIVE] Created unified heartbeat task: 4f2c1a...
[REACT] starting...
[WORKFLOW: SIMPLE TASK] Query: Execute due proactive tasks (3 daily)
```

## Routing rules

`react()` checks trigger type and session state **in this order** — the first match wins:

| Order | Condition | Workflow |
|---|---|---|
| 1 | `trigger.payload.type == "memory_processing"` | **Memory** — distils `EVENT_UNPROCESSED.md` into `MEMORY.md` |
| 2 | `trigger.payload.type` in `proactive_heartbeat` / `proactive_planner` | **Proactive** — see [Proactive mode](../modes/proactive.md) |
| 3 | Session is active AND `STATE.gui_mode == True` | **GUI task** — vision-driven desktop control |
| 4 | Session is active AND task is **complex** | **Complex task** — todo-managed multi-step |
| 5 | Session is active AND task is **simple** | **Simple task** — linear run-to-completion |
| 6 | fallthrough | **Conversation** — no active task, reply or create one |

## The action beat

Inside workflows #3–#6, every iteration runs four phases:

1. **`_select_action(trigger_data)`** — LLM chooses one or more actions (and their inputs) from the library. See [Skill & action selection](skill-selection.md).
2. **`_retrieve_and_prepare_actions(...)`** — resolves each selected action by name, binds its inputs, and wires the `parent_id` so child events link to their parent.
3. **`_execute_actions(...)`** — runs them, collects outputs, records events onto the stream.
4. **`_finalize_action_execution(...)`** — updates the session pointer (a new `task_id` may have been created), cleans up caches.

Conversation, simple, and complex modes all share this beat — they differ only in what caching strategy is used and whether todos are tracked. See [Task modes](../modes/index.md) for the differences.

## Knobs

Configuration that changes how the loop behaves lives in [`app/config/settings.json`](../configuration/config-json.md):

```json
{
  "memory":    { "enabled": true },
  "proactive": { "enabled": true },
  "gui":       { "enabled": false }
}
```

- Disable **memory** → memory workflow skipped, triggers typed `memory_processing` no-op.
- Disable **proactive** → proactive triggers logged then skipped.
- Disable **gui** → GUI mode branch never taken; vision tasks fall back to text.

## Waiting-for-reply behavior

If a task is marked `waiting_for_user_reply` and a trigger fires with no user message, the loop **re-schedules** itself with a 3-hour delay. This lets long-running interactive tasks pause until the user replies, without blocking the agent.

## Error handling

Every `react()` call is wrapped in try/except. Errors are caught by `_handle_react_error`, logged, and the session is cleaned up in `finally`. The next trigger starts from a clean slate.

## Related

- [Triggers](trigger.md) — what wakes the loop up
- [Task sessions](task-session.md) — the unit the loop operates on
- [Event stream](event-stream.md) — where the loop's output lands
- [Task modes](../modes/index.md) — the six workflow variants
- [Actions](action.md) — the vocabulary inside every workflow
