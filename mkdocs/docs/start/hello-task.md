# Your first task

Onboarding is done. Now make CraftBot do something useful.

## A one-shot request

Simplest thing first — a one-liner:

> *"What's the weather in Tokyo right now?"*

Expected flow:

1. Agent parses the message → [conversation workflow](../modes/index.md)
2. Picks `task_start` with `mode: "simple"`
3. New task starts → picks `web_search` (or a weather skill if enabled)
4. Gets the result, calls `send_message`, task completes

You see the weather in the chat window. Time: ~5-10 seconds.

## A multi-step task

Now something where the agent has to **plan**:

> *"Research three AI-agent frameworks, compare them by popularity, license, and extensibility, and save a summary as `frameworks.md` in the workspace."*

Expected flow:

1. Conversation → `task_start` with `mode: "complex"` (the agent detects the work is multi-step)
2. First iteration: `task_update_todos` creates a plan:
    - [ ] Search for popular AI-agent frameworks
    - [ ] Fetch comparisons from top 3
    - [ ] Draft the summary
    - [ ] Save to workspace
3. Iterates through the todos, one action per iteration
4. Final: `write_file` → `agent_file_system/workspace/frameworks.md`

You can watch the [todos](../modes/complex-task.md) update in the UI in real-time.

## Slash commands you'll use early

```
/help                # list every command
/menu                # open the settings panel (models, integrations, skills, MCP)
/cred status         # see connected integrations
/skill list          # see available skills
/reset               # clear the current session
```

Full catalogue: [Built-in commands](../commands/builtin.md).

## Connect an integration

Most users want to connect one integration on day one. The easiest is Google:

```
/google login
```

A browser tab opens, you click Approve, and Gmail / Calendar / Drive actions become available. Try:

> *"Summarize my unread emails from the last 24 hours."*

See [Connections](../connections/index.md) for every integration.

## Run a proactive task

Open [`agent_file_system/PROACTIVE.md`](../concepts/agent-file-system.md), add:

```yaml
### [DAILY] Morning summary
```yaml
id: morning_summary
frequency: daily
time: "08:00"
enabled: true
priority: 50
permission_tier: 1
instruction: |
  Summarize my unread emails, open PRs, and today's calendar events.
  Send via chat.
```
```

Save the file. With [proactive mode](../modes/proactive.md) enabled, the heartbeat will pick this up tomorrow at 8 AM.

## What to try next

| Want to… | Go to |
|---|---|
| Understand how it works | [Concepts](../concepts/index.md) |
| Run it always-on | [Service mode](service-mode.md) |
| Add your own capability | [Custom action](../develop/custom-action.md) |
| Connect Slack / Telegram / … | [Connections](../connections/index.md) |

## If it breaks

- `tail -f logs/*.log` for raw logs
- `/menu` → Logs panel for the UI version
- [Troubleshooting](../troubleshooting/index.md) for common failure patterns
