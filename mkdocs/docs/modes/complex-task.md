# Complex task mode

Complex task mode is the **planning** variant of the [agent loop](../concepts/agent-loop.md). The agent breaks the work into a **todo list**, iterates through it, and updates its own progress — one action beat per todo, with room to revise the plan as it learns. This is how CraftBot handles multi-step work like "research X, write a summary, DM it to Bob."

## Beginner mental model

- A [task](../concepts/task-session.md) is created with `mode: "complex"`.
- The first iteration populates `todos: [TodoItem, ...]` via the `task_update_todos` action.
- Each subsequent iteration picks **the current in-progress todo** (or the next pending one), selects an action to advance it, and either marks it completed or updates the plan.
- The task completes when **all todos are `completed`** and the agent calls `task_complete`.

The agent owns the plan. You can see it at any time in the UI or in the task's `todos` field.

## Inspect it now

Watch the workflow transition and todo updates:

```bash
tail -f logs/*.log | grep -E "COMPLEX TASK|task_update_todos"
```

## Example

You: *"Research Q2 earnings, compare to Q1, DM Bob the summary"*

```text
[WORKFLOW: COMPLEX TASK] Query: Research Q2 earnings, ...
[PARALLEL] Complex task mode selected 1 action(s): ['task_update_todos']
[ACTION] task_update_todos -> ok (4 todos set)
  [>] Fetch Q2 earnings report
  [ ] Fetch Q1 earnings for comparison
  [ ] Draft summary with key deltas
  [ ] DM Bob on Slack

[WORKFLOW: COMPLEX TASK] Query: current todo: Fetch Q2 earnings report
[PARALLEL] Complex task mode selected 1 action(s): ['web_search']
[ACTION] web_search -> ok (5 results)
[ACTION] task_update_todos -> ok (todo 1 completed, todo 2 in-progress)
...
```

## TodoItem

The unit of plan. Each is a small dataclass:

```python
@dataclass
class TodoItem:
    content: str                                    # Imperative: "Run tests"
    status: Literal["pending", "in_progress", "completed"]
    active_form: Optional[str]                      # Present-continuous: "Running tests"
    id: str                                         # UUID
```

Exactly **one** todo should be `in_progress` at any time. The agent is trained to mark a todo `in_progress` when it starts, and `completed` as soon as it finishes — no batching.

## The action beat

Same four phases as [simple task](simple-task.md), but with [`SELECT_ACTION_IN_TASK_PROMPT`](../concepts/prompt.md) which teaches the agent to:

1. Look at the current todo
2. Pick an action that advances it
3. Possibly update todos in the same turn (parallel action)

## Current-todo selection

`Task.get_current_todo()` picks the next todo to work on:

1. **Prefer `in_progress`** — continue where you left off
2. **Fallback to first `pending`** — if no in-progress exists
3. **Return None** — all complete → agent should call `task_complete`

## Plan revision

The agent can call `task_update_todos` at any time to:

- **Add** new todos (the plan got bigger)
- **Reorder** pending todos (priorities changed)
- **Remove** obsolete todos (the user pivoted)
- **Edit content** of a todo (clearer wording)

This is how an agent that hits an obstacle adapts — e.g. "I can't find the Q2 report" → adds `Check our shared drive for Q2 report` as a new todo.

## Session caching

Complex tasks benefit most from session-level prompt caching. Because the iteration loop can span dozens of turns, reusing the cached prefix is dramatic — 10-20× cost reduction over non-cached calls on supporting providers (Anthropic, Gemini, BytePlus). See [Context engine](../concepts/context-engine.md).

## Loop safety

Two guards prevent runaway tasks:

| Limit | Default | Where |
|---|---|---|
| `MAX_ACTIONS_PER_TASK` | `500` | [`app/config.py`](../configuration/config-json.md#constants-not-in-json) |
| `MAX_TOKEN_PER_TASK` | `12_000_000` | [`app/config.py`](../configuration/config-json.md#constants-not-in-json) |

Hitting either limit ends the task with an error.

## Promoting from simple → complex

Mid-task, if the agent calls `task_update_todos` on a simple-mode task, the task is promoted to complex. This is the most common way complex tasks get created — not upfront, but on demand when the agent realises the work needs planning.

## Demoting complex → simple

Not supported. Once a task has todos, it stays complex until completion.

## Related

- [Simple task](simple-task.md) — when no todos needed
- [Task sessions](../concepts/task-session.md) — the underlying data model
- [Skill & action selection](../concepts/skill-selection.md) — the `SELECT_ACTION_IN_TASK_PROMPT`
- [Agent loop](../concepts/agent-loop.md) — the shared cycle
