# Agent file system

The agent file system is CraftBot's **persistent memory layout on disk** — a directory of markdown files that the agent reads from and writes to. It's how the agent remembers who it is, who you are, what you've asked for, what it's done, and what's on its mind.

## Beginner mental model

- A **folder** at `agent_file_system/` in the project root.
- Roughly **10 markdown files**, each with a distinct role.
- Plus a `workspace/` subdirectory for scratch/tmp files.
- The agent treats these files as its **knowledge base** — they're injected into prompts (via the [context engine](context-engine.md)), indexed by [memory](memory.md), and modified by actions like `stream_edit` and `write_file`.

Edit them, and the agent's behaviour changes. Most fields are filled by [onboarding](../start/onboarding.md) or the agent itself.

## Inspect it now

```bash
ls agent_file_system/
```

```text
AGENT.md                        # Agent identity, role, protocols
USER.md                         # User profile, preferences, goals
MEMORY.md                       # Distilled long-term memories
EVENT.md                        # Raw event log
EVENT_UNPROCESSED.md            # Events awaiting memory distillation
TASK_HISTORY.md                 # Completed tasks
CONVERSATION_HISTORY.md         # User ↔ agent transcripts
PROACTIVE.md                    # Scheduled autonomous tasks
SOUL.md                         # Persistent personality traits
FORMAT.md                       # Message formatting standards
MISSION_INDEX_TEMPLATE.md       # Template for multi-mission indexing
workspace/                      # Scratch dir for task outputs
```

## The files

| File | Written by | Read by | Purpose |
|---|---|---|---|
| **AGENT.md** | Human / agent | Every LLM call (via `AGENT_INFO_PROMPT`) | Identity, role, error-handling protocol, self-improvement workflow |
| **USER.md** | Onboarding / user | Every LLM call (via `USER_PROFILE_PROMPT`) | Full name, email, timezone, communication preferences, life goals |
| **MEMORY.md** | Memory distillation | Via [memory_search](memory.md) retrieval | Long-term important facts, decisions, history |
| **EVENT.md** | Agent | Humans only (you) | Raw chronological log of everything |
| **EVENT_UNPROCESSED.md** | Agent | Memory distillation task | Events awaiting promotion to MEMORY.md |
| **TASK_HISTORY.md** | Task manager | Humans / memory search | Finished task records with summaries |
| **CONVERSATION_HISTORY.md** | UI layer | Context for follow-ups | User ↔ agent conversation transcripts |
| **PROACTIVE.md** | Human / planner | [Proactive heartbeat](../modes/proactive.md) | Scheduled recurring tasks with rubrics |
| **SOUL.md** | Human / agent | Every LLM call (via `SOUL_PROMPT`) | Persistent personality / character traits |
| **FORMAT.md** | Human | Agent reads when formatting output | Message format standards |

## workspace/

The scratch directory. Tasks write temp files here (report drafts, downloaded PDFs, screenshots) when the output doesn't belong in the permanent file system. Path: `agent_file_system/workspace/`, exposed as [`AGENT_WORKSPACE_ROOT`](../configuration/config-json.md) in code.

**Lifecycle**: not auto-cleaned. You're free to periodically purge it. Per-task `temp_dir` directories inside workspace are cleaned when the task ends — but files the agent explicitly wrote to workspace are kept.

## How the files feed the LLM

The [context engine](context-engine.md) injects several files directly into the system prompt:

```
System prompt:
  AGENT_ROLE_PROMPT
+ AGENT_INFO_PROMPT (fills from AGENT.md)
+ SOUL_PROMPT (fills from SOUL.md)
+ AGENT_FILE_SYSTEM_CONTEXT_PROMPT (lists every file + schema)
+ USER_PROFILE_PROMPT (fills from USER.md)
+ POLICY_PROMPT
+ ENVIRONMENTAL_CONTEXT_PROMPT
```

`MEMORY.md` and the rest are *not* injected wholesale — the agent retrieves from them via `memory_search` when it needs to.

## Editing safely

You can hand-edit any file. The agent picks up changes on the next trigger (no restart needed). Two patterns:

- **AGENT.md / SOUL.md / PROACTIVE.md / FORMAT.md** — you edit these by hand or ask the agent to.
- **EVENT.md / EVENT_UNPROCESSED.md / TASK_HISTORY.md / CONVERSATION_HISTORY.md / MEMORY.md** — the agent writes these. Editing by hand works but may get overwritten.

!!! warning "Preserve HTML comment markers in PROACTIVE.md"
    `PROACTIVE.md` uses HTML comment markers like `<!-- PROACTIVE_TASKS_START -->` that the [proactive parser](../modes/proactive.md) depends on. Don't remove them.

## Templates

The first-run onboarding copies templates from `app/data/` into `agent_file_system/`. If you delete a file, the agent regenerates it from the template.

## Agent bundle overrides

A [subclassed agent bundle](../develop/custom-agent.md) can point to its own file system via `data_dir` in [`config.yaml`](../configuration/agent-config-yaml.md):

```yaml
data_dir: agents/dog_agent/data/
```

The bundled file system replaces the default one for that agent.

## Related

- [Agent MD files reference](../reference/agent-md-files.md) — schema of each file
- [Memory](memory.md) — how these files get indexed and retrieved
- [Context engine](context-engine.md) — how they're injected into prompts
- [Custom agent](../develop/custom-agent.md) — per-agent file system overrides
