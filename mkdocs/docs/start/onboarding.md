# Onboarding

The first time you run `python run.py`, CraftBot walks you through a wizard. Two phases:

- **Hard onboarding** — a must-complete form: API keys, agent name, interface modes.
- **Soft onboarding** — a conversational follow-up where the agent fills in [USER.md](../reference/agent-md-files.md) over your first few exchanges.

## Beginner mental model

- Onboarding **writes to disk**: [`settings.json`](../configuration/config-json.md), [`agent_file_system/USER.md`](../reference/agent-md-files.md), and credential files under [`app/credentials/`](../connections/credentials.md).
- It's **idempotent** — re-run it with `/menu` → Re-onboard to change anything.
- It's **resumable** — close the app mid-wizard, it picks up where you left off.

## Hard onboarding steps

| Step | What you're asked | Stored in |
|---|---|---|
| **Welcome** | Accept the license, choose OS language | `settings.json` → `general.os_language` |
| **Agent name** | Name your agent (default: "CraftBot") | `settings.json` → `general.agent_name` |
| **LLM provider** | Pick from `anthropic`, `openai`, `google`, `byteplus`, `remote` (Ollama) | `settings.json` → `model.llm_provider` |
| **API key** | Paste your key | `settings.json` → `api_keys.*` (or env var if set) |
| **VLM provider** | (Optional) different provider for vision | `settings.json` → `model.vlm_provider` |
| **Memory** | Enable the [memory system](../concepts/memory.md)? | `settings.json` → `memory.enabled` |
| **Proactive** | Enable [proactive mode](../modes/proactive.md)? | `settings.json` → `proactive.enabled` |
| **Skills** | Pick which [skills](../develop/skills/index.md) to enable | `skills_config.json` |
| **MCP** | (Optional) add MCP servers | `mcp_config.json` |
| **Integrations** | (Optional) connect Google / Slack / etc. | per-integration credential store |

Each step has a **skip** button — you can always come back via `/menu`.

## Soft onboarding

After hard onboarding, the agent asks you a few questions over chat:

- Your name, preferred name, email
- Location and timezone
- Communication preferences (tone, style, platform)
- Life goals
- Agent interaction preferences (proactive approval tier)

Answers populate [`USER.md`](../reference/agent-md-files.md) — the agent reads this file in every prompt, so tailoring here noticeably shifts its style.

Soft onboarding doesn't block — you can start tasks before finishing it. The agent will nudge you periodically with the next question.

## Re-running

```
/menu → Settings → Re-run onboarding
```

Or manually:

```bash
rm app/config/settings.json   # to redo hard onboarding from scratch
rm agent_file_system/USER.md  # to redo soft onboarding
```

*(First re-run after a `rm` still preserves other data — only the wiped files are re-initialized.)*

## Inspect it now

```
/menu
```

opens the settings panel, which is the onboarding UI but with "save" instead of "next."

## Under the hood

Hard onboarding lives in [`app/onboarding/`](../concepts/agent-file-system.md). Each step is a `StepProtocol` with:

- A question text
- A handler that validates input
- A "persist" hook that writes to disk

Add a new step by implementing the protocol — see [Custom agent](../develop/custom-agent.md) for when this is useful.

## Related

- [Install](install.md) — what you do before onboarding
- [USER.md reference](../reference/agent-md-files.md) — what soft onboarding fills in
- [settings.json](../configuration/config-json.md) — what hard onboarding writes
- [Your first task](hello-task.md) — what to do after onboarding
