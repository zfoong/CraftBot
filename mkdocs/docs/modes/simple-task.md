# Simple task mode

Simple task mode is the **streamlined** variant of the [agent loop](../concepts/agent-loop.md). The agent picks one (or a few parallel) actions, runs them, returns the result — no todos, no planning, no loops. Best for one-shots and quick lookups.

## Beginner mental model

- A [task](../concepts/task-session.md) is created with `mode: "simple"`.
- The agent enters `_handle_simple_task_workflow`, which runs **one action beat** (`select → prepare → execute → finalize`) and exits.
- If the agent needs another turn, a follow-up [trigger](../concepts/trigger.md) is queued and another simple-task iteration runs.
- Todos exist on the Task dataclass but are never auto-populated — simple tasks usually finish before they'd be useful.

## Inspect it now

The workflow logs a single line when it enters:

```bash
tail -f logs/*.log | grep "WORKFLOW: SIMPLE TASK"
```

## Example

You: *"send a Slack DM to Bob saying I'm running late"*

```text
[WORKFLOW: CONVERSATION] Query: send a Slack DM to Bob ...
[PARALLEL] Conversation mode selected 1 action(s): ['task_start']
[TASK] Created task abc123 mode=simple action_sets=[core]
[WORKFLOW: SIMPLE TASK] Query: send a Slack DM to Bob ...
[PARALLEL] Simple task mode selected 1 action(s): ['send_slack_message']
[ACTION] send_slack_message -> ok (channel=D0123, ts=1713...)
[TASK] abc123 completed
```

One task. One action. Done.

## When simple mode is chosen

The LLM picks `mode: "simple"` when creating the task via `task_start`. The decision is shaped by [`SELECT_ACTION_PROMPT`](../concepts/prompt.md), which trains the model toward:

- Single-request operations (`"send X"`, `"look up Y"`, `"what's the weather"`)
- Clear-cut integrations (`"DM Alice on Telegram"`)
- Small, well-scoped follow-ups (`"also email her the Zoom link"`)

If the request is multi-step, research-heavy, or needs verification, the LLM picks `complex` instead.

## The action beat

Simple-task iterations use the same four-phase beat as [complex task](complex-task.md):

1. `_select_action(trigger_data)` with [`SELECT_ACTION_IN_SIMPLE_TASK_PROMPT`](../concepts/prompt.md)
2. `_retrieve_and_prepare_actions`
3. `_execute_actions`
4. `_finalize_action_execution`

The difference is the prompt — simple mode's prompt omits todo management instructions, keeping the LLM focused on "pick an action, run it, return the result."

## Session caching

Simple tasks benefit from **session-level prompt caching** via the [context engine](../concepts/context-engine.md). Each iteration only appends the new events delta to the cached prefix, not the full history. This keeps per-call cost low even across multiple turns.

## Completion

A simple task completes when the agent calls `task_complete` — typically the second action picked after the work one (e.g. `send_slack_message` then `task_complete`). The agent can also end with a `send_message` reply to the user and skip `task_complete`, which transitions the session back to conversation mode.

## Promoting to complex

If mid-task the agent realises the work is deeper than expected, it can call `task_update_todos` with a todo list — this effectively promotes the task to complex mode for subsequent iterations. The task's `mode` field is updated.

## Knobs

Simple task mode has no dedicated knobs beyond the task-level settings:

- `action_sets` — scope of available actions
- `selected_skills` — prompt fragments injected per iteration
- `waiting_for_user_reply` — pauses trigger scheduling

See [Task sessions](../concepts/task-session.md) for the full field list.

## Related

- [Complex task](complex-task.md) — when you need todos + planning
- [Agent loop](../concepts/agent-loop.md) — the shared cycle
- [Actions](../concepts/action.md) — the vocabulary used in every iteration
