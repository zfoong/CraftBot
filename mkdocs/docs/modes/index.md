# Task modes

CraftBot runs tasks in one of four modes. The agent picks the mode automatically based on the task, but you can override with directives. Each mode is a different variant of the [agent loop](../concepts/agent-loop.md).

<div class="grid cards" markdown>

- :material-play-circle-outline:{ .lg .middle } __[Simple task](simple-task.md)__

    ---

    Linear todo list, run to completion. Best for short, well-defined requests.

- :material-graph-outline:{ .lg .middle } __[Complex task](complex-task.md)__

    ---

    Iterative action loop with dynamic todos. For multi-step, open-ended work.

- :material-cogs:{ .lg .middle } __[Special workflows](special-workflows.md)__

    ---

    Named workflows for memory processing, proactive handling, GUI control.

- :material-bell-ring-outline:{ .lg .middle } __[Proactive](proactive.md)__

    ---

    Heartbeat, planner, and scheduler — the agent initiates tasks on its own.

</div>

## Which mode runs?

| Signal | Mode |
|---|---|
| One-shot question or quick action | Simple task |
| "Research X, write a report, send it to Bob" | Complex task |
| Incoming event, midnight memory distillation, GUI-required task | Special workflow |
| Idle tick, scheduled event, learned preference | Proactive |

## Related

- [Agent loop](../concepts/agent-loop.md) — the primitive every mode extends
- [Triggers](../concepts/trigger.md) — what starts a task in each mode
- [Actions](../concepts/action.md) — the vocabulary used in every mode
