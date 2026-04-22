# Agent MD files

Schema and writing conventions for every file in [`agent_file_system/`](../concepts/agent-file-system.md).

All files use **plain markdown** — no JSON, no YAML (except where noted). This is deliberate: the files are meant to be readable and editable by humans and the agent equally.

## AGENT.md

**Written by:** humans / agent · **Read by:** every LLM call (via `AGENT_INFO_PROMPT`)

Defines the agent's identity and protocols. No fixed schema — the file is free-form markdown. Typical sections:

- Identity (who the agent is, what it can do)
- Error handling protocol
- File handling rules
- Self-improvement workflow (when to install MCP servers / skills)
- Policies (what not to do)

The default AGENT.md shipped with CraftBot has all of these. Custom agents override the identity section for their persona.

## USER.md

**Written by:** onboarding / user · **Read by:** every LLM call (via `USER_PROFILE_PROMPT`)

Fixed schema — the [onboarding wizard](../start/onboarding.md) fills this on first launch:

```markdown
## Identity
- **Full Name:** ...
- **Preferred Name:** ...
- **Email:** ...
- **Location:** ...
- **Timezone:** (inferred from location)
- **Job:** ...

## Communication Preferences
- **Language:** en
- **Preferred Tone:** (casual | formal | concise | verbose)
- **Response Style:** (bullet points | prose | short | long)
- **Preferred Messaging Platform:** (Slack | Telegram | WhatsApp | CraftBot UI)

## Agent Interaction
- **Prefer Proactive Assistance:** (yes | no)
- **Approval Required For:** (list of sensitive operations)

## Life Goals
...

## Personality
...
```

## MEMORY.md

**Written by:** daily memory distillation task · **Read by:** via [`memory_search`](../concepts/memory.md)

Freeform markdown with sections. The distiller appends new entries under headers like:

```markdown
### <YYYY-MM-DD> <short title>
<body describing what happened / was learned>
```

The memory indexer chunks by section header, so keep each entry under one H3.

## EVENT.md

**Written by:** agent (continuously) · **Read by:** humans + memory distiller

Raw chronological log. Every significant interaction — user messages, tasks started/completed, integrations connected — gets a line. Not for the LLM to re-read; for humans auditing what the agent has been doing.

Grows unbounded unless you truncate it periodically.

## EVENT_UNPROCESSED.md

**Written by:** agent · **Read by:** daily memory distillation

Events the distiller has not yet reviewed. The distillation task:

1. Reads this file
2. Scores each event for long-term value
3. Writes keepers to MEMORY.md
4. Clears EVENT_UNPROCESSED.md

You should not edit this file manually.

## TASK_HISTORY.md

**Written by:** [TaskManager](../concepts/task-session.md) on `task_end` · **Read by:** humans + memory search

One section per completed task:

```markdown
### <YYYY-MM-DD HH:MM> <task name> [id=<uuid>]
- **Instruction:** <original instruction>
- **Mode:** simple | complex
- **Duration:** N minutes
- **Outcome:** <final_summary>
- **Todos:**
  - [x] Step 1
  - [x] Step 2
```

## CONVERSATION_HISTORY.md

**Written by:** UI layer · **Read by:** context for follow-ups

Multi-turn transcripts for context continuation. Format:

```markdown
### <YYYY-MM-DD HH:MM> conversation

**user:** question
**agent:** answer

**user:** follow-up
**agent:** reply
```

## PROACTIVE.md

**Written by:** humans / proactive planner · **Read by:** [proactive heartbeat](../modes/proactive.md)

See [Proactive](../modes/proactive.md) for the full schema — it uses YAML fenced inside markdown, with HTML comment markers (`<!-- PROACTIVE_TASKS_START -->`, etc.) that the parser depends on. **Don't remove the markers.**

## SOUL.md

**Written by:** humans / agent · **Read by:** every LLM call (via `SOUL_PROMPT`)

Persistent personality traits that persist across all tasks. Keep it terse — just 3–5 paragraphs defining tone, quirks, and values. Unlike AGENT.md (which is about what to do), SOUL.md is about *how the agent feels*.

## FORMAT.md

**Written by:** humans · **Read by:** agent when formatting output

Output conventions — bullet styles, heading depth, emoji usage, code-block fencing. The agent reads this when deciding how to render `send_message` output.

## MISSION_INDEX_TEMPLATE.md

**Template** used when the agent starts a multi-session mission (research projects that span days). Copied into a subdirectory and filled in over time.

## workspace/

A scratch directory. No schema. Tasks drop temp files here (drafts, downloaded content, screenshots). Lifecycle:

- Per-task `temp_dir` subdirectories are cleaned up when the task ends
- Files written directly to `workspace/` persist until manually removed

## Agent-bundle overrides

A [custom agent](../develop/custom-agent.md) with `data_dir: agents/my_agent/data/` uses its own files at that path. The schemas are identical.

## Related

- [Agent file system concept](../concepts/agent-file-system.md) — what / why / how it's used
- [Memory](../concepts/memory.md) — how these files get indexed
- [Context engine](../concepts/context-engine.md) — how the files are injected into prompts
