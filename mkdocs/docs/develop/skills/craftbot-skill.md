# Write a CraftBot skill

A **skill** is a bundle of strategy — a `skill.md` + optional scripts — that teaches the agent *how* to use existing [actions](../../concepts/action.md) for a specific domain. Unlike actions (which add capability), skills add **guidance**.

## What you're building

A folder under `skills/<your-skill>/` containing:

- `skill.md` — YAML frontmatter + markdown instructions
- *(optional)* `scripts/` — helper shell scripts the skill calls via `run_shell`

At runtime, the agent's [SkillManager](../../concepts/skill-selection.md) discovers your skill. Tasks opt in by setting `selected_skills: ["<name>"]` — the skill's instructions then inject into the system prompt for that task.

## Step 1 — Scaffold

```bash
mkdir -p skills/daily-standup-summary
touch skills/daily-standup-summary/skill.md
```

The folder name is your skill id.

## Step 2 — Write `skill.md`

```markdown
---
name: daily-standup-summary
description: |
  Generate a daily standup summary from recent events and commit activity.
  Use for morning check-ins, team updates, and progress reports.
os:                          # optional — restrict to specific OSes
  - linux
  - darwin
binaries:                    # optional — require binaries to be available
  - git
config_deps:                 # optional — require settings.json fields
  - github.enabled
---

# Daily Standup Summary

When this skill is active, follow these steps:

1. **Read recent events** — `read_file agent_file_system/EVENT.md` and scan the last 24 hours.
2. **Check git activity** — `run_shell "git log --since='24 hours ago' --oneline"` in each tracked repo.
3. **Collate into three sections**:
   - Done yesterday
   - Plan for today
   - Blockers
4. **Keep the output terse** — bullet points, not paragraphs.
5. **Send via `send_message`** — or the preferred platform action if the user has integrations connected.

## Don'ts

- Don't list every commit — only meaningful ones.
- Don't invent activity if sources are empty; say "no activity detected" instead.
```

## Step 3 — Register (auto-discovery)

There is no manual registration. On startup the SkillManager scans:

- `skills/` at the project root (user-provided skills)
- Plus any paths configured in `app/config/skills_config.json`

Your new skill is discovered automatically and available for selection.

## Step 4 — Reload the session

Skills are **hot-reloaded** — saving `skill.md` makes the skill available on the next task. No restart needed.

```
[SkillManager] Loaded 42 skills (3 added, 0 removed)
```

## Step 5 — Test

### Force-select the skill

When creating a task via `/agent_command` or Python:

```python
task_manager.create_task(
    task_name="Morning standup",
    task_instruction="Produce today's standup summary",
    mode="simple",
    selected_skills=["daily-standup-summary"],
)
```

### From chat

> *"Using the daily-standup-summary skill, give me today's update."*

The agent detects the skill reference, enables it for the task, and follows its instructions.

### List skills

```
/skill list
```

Shows your new skill with its enabled state.

## Metadata reference

| Field | Type | Purpose |
|---|---|---|
| `name` | str | Must match folder name |
| `description` | str | **Teaches the LLM when to opt in** — similar to action description |
| `os` | list | Restrict to `linux`, `darwin`, `windows` |
| `binaries` | list | Required executables (skill is skipped if missing) |
| `config_deps` | list | Required [settings.json](../../configuration/config-json.md) fields |
| `allow_tools` | list | Optional allowlist of actions this skill can call (narrows the router) |

## Load order / precedence

1. **Agent-bundle skills** (via `selected_skills` in `config.yaml`) — always on for that agent
2. **Task-selected skills** (`selected_skills` on the `Task` dataclass) — per-task
3. **Auto-detected by LLM** — if a skill's description matches the user's query, the LLM can opt in via `task_update_todos` / `set_mode`

Multiple skills can be active simultaneously — their instructions are concatenated into the system prompt.

## Scripts

If your skill bundles shell scripts:

```
skills/daily-standup-summary/
├── skill.md
└── scripts/
    └── collect_repos.sh
```

Reference them from the skill.md:

> *"Run `skills/daily-standup-summary/scripts/collect_repos.sh` to find all tracked repos."*

The agent invokes them via [`run_shell`](../../commands/cli-anything.md).

## Browse examples

The `skills/` directory has dozens of working examples — `ai-ppt-generator`, `baidu-search`, `anki-connect`, `apple-notes`, etc. Read a few to learn idioms.

## Related

- [External skills](external-skill.md) — load third-party skills
- [Custom action](../custom-action.md) — add capability rather than strategy
- [Skill & action selection](../../concepts/skill-selection.md) — how skills are picked
- [Skills overview](index.md)
