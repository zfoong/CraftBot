# Quickstart

Zero to running agent in 5 minutes.

## Prerequisites

- CraftBot [installed](install.md)
- An LLM API key in hand

## 5-step flow

### 1. Clone + install

```bash
git clone https://github.com/zfoong/CraftBot.git
cd CraftBot
python install.py
```

### 2. Run

```bash
python run.py           # browser (needs Node.js)
# OR
python run.py --tui     # terminal UI (no Node.js)
```

### 3. Onboarding wizard

First launch opens the [onboarding wizard](onboarding.md):

- Pick an LLM provider (Anthropic / OpenAI / Google / BytePlus / Ollama)
- Paste your API key
- Give the agent a name
- (Optional) Enable memory, proactive mode, and skills

Click **Finish**. The agent starts up.

### 4. Send a message

```
You: what's the weather in Tokyo
```

Watch the agent plan, pick actions (`web_search` or a weather skill), and reply.

### 5. Try a complex task

```
You: research the top 3 Python web frameworks, summarize the differences,
     and save the summary as frameworks.md in the workspace
```

Now you'll see **todos** appear, actions fire in sequence, and a file written to `agent_file_system/workspace/frameworks.md`.

## What just happened?

| Step | What CraftBot did |
|---|---|
| 1–2 | Installed deps, launched [one of the interfaces](../interfaces/index.md) |
| 3 | Wrote [settings.json](../configuration/config-json.md) with your provider + keys |
| 4 | Routed the message through the [agent loop](../concepts/agent-loop.md) → [Conversation workflow](../modes/index.md) → `task_start` |
| 5 | Created a [complex task](../modes/complex-task.md) with todos, iterated through actions |

## Next

- [Your first task](hello-task.md) — more examples
- [Service mode](service-mode.md) — run it as a background daemon
- [Concepts](../concepts/index.md) — understand what's happening under the hood
- [Connections](../connections/index.md) — connect Slack, Google, Discord, …

## Stuck?

- [Troubleshooting](../troubleshooting/index.md)
- [Discord community](https://discord.gg/ZN9YHc37HG)
- [GitHub issues](https://github.com/zfoong/CraftBot/issues)
