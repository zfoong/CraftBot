# Proactive

Proactive mode lets CraftBot act on its own — reminding you, checking inboxes, drafting summaries, running audits — without you asking. It's built from three pieces: a **heartbeat** that fires every 30 minutes, a **planner** that updates the plan periodically, and a **scheduler** that fires cron-style.

## The core idea

Proactive behaviour is driven by two files:

- **`agent_file_system/PROACTIVE.md`** — human-readable YAML-in-markdown listing **recurring tasks** (hourly/daily/weekly/monthly). Edited by you or the planner.
- **`app/config/scheduler_config.json`** — the scheduler's registry of **when the agent wakes up** (heartbeat, planner, one-off schedules).

Every 30 minutes the heartbeat fires, reads PROACTIVE.md, finds due tasks, and executes them. Once a day/week/month, the planner fires and updates PROACTIVE.md based on what happened recently.

## Scenarios

### 1) Workstation assistant (the default)

Heartbeat every 30 min + daily planner. The agent runs on your laptop; schedules only fire when it's running. Best for a personal assistant you interact with daily.

### 2) Always-on server

Same config but on a persistent machine (VPS, home server) via [service mode](../start/service-mode.md). Heartbeats fire reliably 24/7, so `daily` tasks fire even when you're not using the agent.

### 3) Bounded proactive (e.g. only work hours)

Add `weekdays_only` and `market_hours_only` conditions to tasks in PROACTIVE.md. Heartbeat still fires every 30 min, but conditions gate which tasks actually run.

## Command flow

```
                  ┌────────────────────┐
                  │ scheduler_config   │
                  │ (every 30min)      │
                  └──────────┬─────────┘
                             ↓ fires trigger (proactive_heartbeat)
                  ┌──────────────────────────┐
                  │ _handle_proactive_workflow│
                  └──────────┬───────────────┘
                             ↓
              reads PROACTIVE.md, collects due tasks
                             ↓
        creates one "Heartbeat" simple-mode task (skill: heartbeat-processor)
                             ↓
                   queued to trigger queue
                             ↓
                   agent loop runs the task
                             ↓
           task executes due proactive tasks, updates outcome_history
```

The planner follows the same flow with `proactive_planner` trigger type and a `{scope}-planner` skill.

## PROACTIVE.md anatomy

```yaml
### [DAILY] Morning inbox summary
```yaml
id: morning_inbox_summary
frequency: daily
time: "08:30"
enabled: true
priority: 50
permission_tier: 1
run_count: 12
conditions:
  - weekdays_only
instruction: |
  1. Connect via Gmail integration.
  2. Fetch unread emails from last 24 hours.
  3. Filter for emails from contacts in CONTACTS.md.
  4. Compile summary with Urgent / Important / FYI sections.
  5. Send summary as chat message.
outcome_history:
  - timestamp: 2026-04-22T08:30:12
    success: true
    result: "Summarized 4 emails (1 urgent, 2 important, 1 FYI)"
```
```

Fields:

| Field | Required | Options |
|---|---|---|
| `id` | yes | snake_case unique identifier |
| `frequency` | yes | `hourly` / `daily` / `weekly` / `monthly` |
| `time` | recommended | `HH:MM` 24-hour |
| `day` | for weekly/monthly | weekday (`monday`-`sunday`) OR date (`1`-`31`) |
| `enabled` | yes | `true` / `false` |
| `priority` | yes | `1` (high) - `100` (low) |
| `permission_tier` | yes | `0` Silent / `1` Notify / `2` Approval / `3` High-risk |
| `conditions` | no | `market_hours_only`, `user_available`, `weekdays_only`, custom |
| `instruction` | yes | Multi-line detailed task spec |

## Decision rubric (proactive scoring)

PROACTIVE.md ships with a five-dimension rubric the planner uses when proposing new tasks:

| Dimension | 1 (Low) | 5 (High) |
|---|---|---|
| **Impact** | Negligible | Critical |
| **Risk** | High risk | No risk |
| **Cost** | Very high | Negligible |
| **Urgency** | Not urgent | Immediate |
| **Confidence** | Unlikely | Certain |

Scoring thresholds:

- **18+** — Strong candidate, execute
- **13–17** — May need user input first, consider asking
- **<13** — Skip or defer

## Permission tiers

How a task interacts with the user before / during / after:

| Tier | Level | Meaning |
|---|---|---|
| 0 | Silent | Searching, drafting, internal ops — no notification |
| 1 | Notify | Inform user of execution and findings — no wait |
| 2 | Approval | Ask for approval before proceeding |
| 3 | High-risk | Explicit detailed approval required (email external parties, change configs) |

User-created proactive tasks are typically tier 0 or 1. System-level or consequential tasks should be tier 2 or 3.

## Heartbeat timing

- Heartbeats fire at `:00` and `:30` every hour (clock-aligned).
- Tasks with a `time` field have a **30-minute grace period** after their target time — miss it, and the task skips until the next window (no catch-up runs).
- `hourly` tasks fire on **every** heartbeat regardless of `time`.

See `RecurringTask.should_run()` in [`app/proactive/types.py`](../concepts/agent-file-system.md) for the exact logic.

## Scheduler expressions

The scheduler supports five schedule types:

| Type | Example raw expression |
|---|---|
| `daily` | `"every day at 07:00"` |
| `weekly` | `"every monday at 09:00"` |
| `interval` | `"every 30 minutes"` (this is how heartbeat is registered) |
| `cron` | `"0 3 * * *"` (3 AM daily — memory distillation) |
| `once` | `"at 2026-05-01T12:00:00Z"` |

Schedules live in [`app/config/scheduler_config.json`](../configuration/config-json.md) and are hot-reloaded.

## Master switch

```json
// settings.json
{ "proactive": { "enabled": true } }
```

Disabling this:

- Heartbeat triggers log and skip — no tasks are created
- Planner triggers log and skip
- Memory distillation is *not* affected (its own toggle)
- One-off scheduled tasks still fire (they're scheduler-driven, not proactive-driven)

## Outcome history

Each `RecurringTask` keeps the last **5** outcomes in `outcome_history` — timestamp, result summary, success flag. The planner reads these to decide whether a task is worth keeping, tuning, or retiring.

## Security rules

!!! warning "Don't remove HTML comment markers"
    `PROACTIVE.md` uses markers like `<!-- PROACTIVE_TASKS_START -->` that the parser depends on. Edit the YAML inside; don't touch the markers.

- **Tier 2/3 tasks** require explicit approval in the UI before each execution — don't rely on proactive-only tier 2+ tasks to run unattended.
- The agent can **edit PROACTIVE.md itself** via the planner — review its edits before enabling new tasks.
- **Conditions** are evaluated in-process; custom conditions that call external services should handle network failures gracefully.

## Related

- [Special workflows](special-workflows.md) — how proactive triggers are routed
- [Agent file system](../concepts/agent-file-system.md) — where PROACTIVE.md lives
- [Memory](../concepts/memory.md) — the other scheduled workflow
- [Service mode](../start/service-mode.md) — running the agent persistently for proactive
- [`settings.json`](../configuration/config-json.md) — `proactive.enabled` master switch
