---
version: 1.0
last_updated: 2026-03-09T20:30:33.334803
---

# Proactive Management

This document defines proactive tasks that the agent executes automatically based on scheduled heartbeats.

## How Proactive Tasks Work

When a scheduled heartbeat fires (hourly, daily, weekly, or monthly), the agent:
1. Reads this PROACTIVE.md file to find tasks matching the current frequency
2. Evaluates each task's conditions and priority
3. Executes enabled tasks according to their permission tier
4. Records outcomes in the task's history

## Permission Tiers

Each task has a permission tier that controls how it interacts with the user:

| Tier | Level | Description | User Interaction |
|------|-------|-------------|------------------|
| 0 | Silent | Searching, analyzing, drafting, internal operations | Proceed without notifying the user |
| 1 | Notify | Inform user of task execution and findings | Inform and proceed without waiting |
| 2 | Approval | Actions that modify state or create artifacts | Ask for approval before proceeding |
| 3 | High-risk | Email external parties, change configs, sensitive ops | Explicit detailed approval required |

**Note:** Tier 0 and 1 are typically used for user-created proactive tasks. Tiers 2-3 are reserved for system-level or high-impact tasks that require user oversight.

## Task Format

Tasks are defined with a markdown header followed by a YAML code block:

**Header format:** `### [FREQUENCY] Task Name`

**YAML fields:**
- `id` (required): Unique identifier (format: `{frequency}_{descriptive_name}`)
- `frequency` (required): One of `hourly`, `daily`, `weekly`, `monthly`
- `instruction` (required): Clear description of what the agent should do
- `enabled`: Whether task is active (default: true)
- `priority`: Execution priority, lower = higher (default: 50)
- `permission_tier`: Permission level 0-3 (default: 1)
- `time`: Time in 24-hour format "HH:MM" (required for daily+)
- `day`: Day name for weekly tasks (e.g., "monday", "sunday")
- `conditions`: List of conditions that must be met
- `run_count`: Number of times task has run (auto-updated)
- `outcome_history`: Recent execution results (auto-updated)

<!-- PROACTIVE_TASKS_START -->

### [HOURLY] System Health Check
```yaml
id: hourly_system_health
frequency: hourly
enabled: true
priority: 40
permission_tier: 0
run_count: 0
instruction: 'Check system health and resource usage. Look for any errors in logs,

  memory issues, or performance problems. Report only if issues are found.

  '
conditions: []
outcome_history: []
```

### [DAILY] Daily world news briefing
```yaml
id: hourly_daily_world_news_briefing
frequency: daily
enabled: true
priority: 50
permission_tier: 1
run_count: 0
instruction: visit oneminutenews.org and check the news digest for me. Then report
  to me.
time: 07:00
conditions: []
outcome_history: []
```

### [DAILY] Morning Briefing
```yaml
id: daily_morning_briefing
frequency: daily
enabled: true
priority: 30
permission_tier: 1
run_count: 0
instruction: 'Prepare a morning briefing for the user. Review:

  - Any scheduled tasks or reminders for today

  - Recent project activity or updates

  - Pending items that need attention

  Present a concise summary to help the user start their day.

  '
time: 08:00
conditions: []
outcome_history: []
```

### [DAILY] End of Day Summary
```yaml
id: daily_eod_summary
frequency: daily
enabled: true
priority: 35
permission_tier: 1
run_count: 0
instruction: 'Summarize the day''s activities:

  - Tasks completed

  - Conversations and decisions made

  - Items to follow up on tomorrow

  Update TASK_HISTORY.md with completed work.

  '
time: '18:00'
conditions: []
outcome_history: []
```

### [WEEKLY] Weekly Review
```yaml
id: weekly_review
frequency: weekly
enabled: false
priority: 25
permission_tier: 1
run_count: 0
instruction: 'Conduct a weekly review:

  - Summarize accomplishments from the past week

  - Review goals and progress

  - Identify blockers or issues that need attention

  - Suggest priorities for the coming week

  Update relevant documentation with findings.

  '
time: '18:00'
day: sunday
conditions: []
outcome_history: []
```

### [MONTHLY] Monthly Retrospective
```yaml
id: monthly_retrospective
frequency: monthly
enabled: false
priority: 20
permission_tier: 1
run_count: 0
instruction: 'Perform a monthly retrospective:

  - Review overall progress on long-term goals

  - Analyze patterns in completed work

  - Identify areas for improvement

  - Update documentation and knowledge base

  - Archive old conversation history if needed

  '
time: '10:00'
conditions: []
outcome_history: []
```

<!-- PROACTIVE_TASKS_END -->

<!-- PLANNER_OUTPUTS_START -->
No planner outputs yet.

<!-- PLANNER_OUTPUTS_END -->
