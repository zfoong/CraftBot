# Special workflows

"Special workflows" are the [agent-loop](../concepts/agent-loop.md) branches that don't start from a user message: **memory distillation**, **proactive processing**, and **GUI task execution**. They get their own `payload.type` on the [trigger](../concepts/trigger.md), short-circuit the normal routing, and run on schedules or events rather than chat.

## Beginner mental model

Three workflow handlers live alongside the user-facing ones (conversation, simple task, complex task):

- `_handle_memory_workflow` — runs when a trigger has `payload.type == "memory_processing"`
- `_handle_proactive_workflow` — runs when a trigger has `payload.type in ("proactive_heartbeat", "proactive_planner")`
- `_handle_gui_task_workflow` — runs when a task is complex AND `STATE.gui_mode == True`

All three **create a regular task** (simple or complex), queue a trigger for it, and let the normal loop do the work. They're just *ways to start tasks automatically*.

## Inspect it now

```bash
tail -f logs/*.log | grep -E "MEMORY|PROACTIVE|GUI MODE"
```

## Memory workflow

Triggered by a scheduled memory-processing task (default **3 AM** via [`MEMORY_PROCESSING_SCHEDULE_HOUR`](../configuration/config-json.md#constants-not-in-json)):

1. Checks `memory.enabled` in [settings.json](../configuration/config-json.md). If off, skip.
2. Creates a simple-mode task with the `memory-processor` skill, action sets `file_operations`, `memory`.
3. Queues a trigger for that task.
4. The task reads [`EVENT_UNPROCESSED.md`](../concepts/agent-file-system.md), scores each event, writes keepers to `MEMORY.md`, clears the unprocessed file.

See [Memory](../concepts/memory.md) for the distillation semantics.

## Proactive workflow

Two variants, both firing from the scheduler:

### Heartbeat

Fires every 30 minutes (`:00` and `:30`):

1. Checks `proactive.enabled`. If off, skip.
2. Collects **all due tasks across every frequency** (hourly, daily, weekly, monthly) via `proactive_manager.get_all_due_tasks()`.
3. Creates **one unified simple-mode task** named `Heartbeat` with the `heartbeat-processor` skill.
4. Task instruction summarizes what's due: `"Execute all due proactive tasks from PROACTIVE.md. Due tasks: 2 daily, 1 weekly (3 total)."`

### Planner

Fires daily / weekly / monthly depending on scope:

1. Creates a simple-mode task named `Day Planner` / `Week Planner` / `Month Planner`.
2. Loads the `{scope}-planner` skill (`day-planner`, `week-planner`, `month-planner`).
3. Instruction: *review recent interactions, update PROACTIVE.md planner section with findings*.

See [Proactive](proactive.md) for the complete model.

## GUI workflow

Triggered when a complex task is already running AND GUI mode is enabled ([settings.json](../configuration/config-json.md) → `gui.enabled`):

1. Each iteration calls `GUIHandler.gui_module.perform_gui_task_step(...)`.
2. The GUI module takes a screenshot, sends it to the [VLM](../providers/vlm.md), and returns a structured action.
3. Actions are pixel-level: click, type, drag, scroll, screenshot.
4. The action is executed via `pyautogui` (or the equivalent platform library).
5. Events are logged into the main [event stream](../concepts/event-stream.md) so the task can iterate.

See [GUI / Vision](../interfaces/gui-vision.md) for requirements and setup.

## Trigger type routing table

| `payload.type` | Workflow | Skip if |
|---|---|---|
| `"memory_processing"` | Memory | `memory.enabled == false` |
| `"proactive_heartbeat"` | Proactive heartbeat | `proactive.enabled == false` OR no due tasks |
| `"proactive_planner"` | Proactive planner | `proactive.enabled == false` |
| `"task_execution"` / `"scheduled"` / *(unset)* | Conversation/simple/complex (normal flow) | — |
| *(implicit — based on STATE.gui_mode)* | GUI task | `gui.enabled == false` |

## Skills used by special workflows

| Skill | Workflow | Purpose |
|---|---|---|
| `memory-processor` | Memory | Step-by-step distillation of EVENT_UNPROCESSED.md |
| `heartbeat-processor` | Proactive heartbeat | Read PROACTIVE.md, filter by time/day, execute |
| `day-planner` / `week-planner` / `month-planner` | Proactive planner | Update PROACTIVE.md plan section |

These skills ship bundled. If you're writing a [custom agent](../develop/custom-agent.md), you can override or replace them.

## Adding your own special workflow

Two ways:

1. **Reuse triggers** — post a trigger with your own `payload.type`, and inject handler logic in an agent subclass's `react()` override.
2. **Use the scheduler** — add a `ScheduledTask` to `scheduler_config.json` that creates tasks on a cron schedule. Simpler and doesn't require a subclass.

## Related

- [Proactive](proactive.md) — the biggest producer of special triggers
- [Memory](../concepts/memory.md) — consumer of the memory workflow
- [GUI / Vision](../interfaces/gui-vision.md) — consumer of the GUI workflow
- [Agent loop](../concepts/agent-loop.md) — the dispatch logic
