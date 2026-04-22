# Event types

Every `kind` that can appear in the [event stream](../concepts/event-stream.md). Custom `kind` values are also allowed — this is the built-in catalogue.

Each event has:

| Field | Type |
|---|---|
| `kind` | str — from this catalogue or any custom string |
| `message` | str — full event payload (may be externalized to disk if > 200k chars) |
| `severity` | `DEBUG` / `INFO` / `WARN` / `ERROR` |
| `ts` | datetime |
| `display_message` | optional UI-friendly variant |
| `action_name` | optional — for action_* kinds |

## Action lifecycle

| `kind` | When | `message` shape |
|---|---|---|
| `action_start` | Just before an action runs | `"<action_name>"` |
| `action_end` | After action completes | `"<action_name> -> <status> (<extras>)"` |
| `action_error` | Exception raised during action | `"<action_name>: <error_class>: <message>"` |
| `action_timeout` | Action exceeded timeout (e.g. `run_shell`) | `"<action_name>: timed out after <N>s"` |

## Task lifecycle

| `kind` | When |
|---|---|
| `task_start` | Task created |
| `task_todo_added` | Todo appended via `task_update_todos` |
| `task_todo_in_progress` | Todo moved to in_progress |
| `task_todo_completed` | Todo marked completed |
| `task_end` | Task completed |
| `task_error` | Task failed |
| `task_paused` | Waiting for user / approval |

## Conversation

| `kind` | When |
|---|---|
| `user_message` | User sent a message (local UI or routed from external platform) |
| `agent_message` | Agent sent a message via `send_message` |
| `agent_reasoning` | Chain-of-thought emitted by the LLM (visible per `/reasoning` directive) |

## Trigger & queue

| `kind` | When |
|---|---|
| `trigger_fired` | Trigger dequeued and about to run |
| `trigger_merged` | Multiple triggers for the same session were combined |
| `trigger_routed` | LLM routed a triggerless message to an existing session |

## Integrations

| `kind` | When |
|---|---|
| `integration_connected` | OAuth / token login succeeded |
| `integration_disconnected` | `/xxx logout` or token expiry |
| `integration_error` | Provider API returned an error |
| `external_message_received` | Message arrived from Slack / Telegram / etc. |

## Memory

| `kind` | When |
|---|---|
| `memory_chunk_added` | Indexer added a chunk to ChromaDB |
| `memory_retrieval` | `memory_search` completed |
| `memory_summary_written` | Daily distillation wrote to `MEMORY.md` |

## Event stream meta

| `kind` | When |
|---|---|
| `stream_summarized` | Rollup into `head_summary` triggered |
| `stream_pruned` | Fallback prune without summary (LLM unavailable) |
| `stream_externalized` | Long message written to temp file |

## Proactive

| `kind` | When |
|---|---|
| `proactive_heartbeat` | Heartbeat trigger fired |
| `proactive_planner` | Planner trigger fired |
| `proactive_task_executed` | One of PROACTIVE.md's tasks ran |
| `proactive_task_skipped` | Task failed its conditions or grace window |

## Severities & filtering

| Severity | Used for |
|---|---|
| `DEBUG` | Low-signal; hidden by default in UI |
| `INFO` | Default for lifecycle events |
| `WARN` | Recoverable anomaly (retry, degraded path) |
| `ERROR` | Action/task failed |

UIs filter by severity — the [TUI](../interfaces/tui.md) has toggles; the [browser](../interfaces/browser.md) has a severity filter.

## Compact-line format

Events appear in [`to_prompt_snapshot()`](../concepts/event-stream.md) as:

```
[2026-04-22 10:14:02] action_start: send_gmail
[2026-04-22 10:14:04] action_end: send_gmail -> ok (message_id=18a2f3e)
```

This is what the LLM sees.

## Related

- [Event stream](../concepts/event-stream.md) — the producer
- [Logs](../concepts/logs.md) — the adjacent operator-facing stream
- [Actions catalogue](actions.md) — actions that produce action_* events
