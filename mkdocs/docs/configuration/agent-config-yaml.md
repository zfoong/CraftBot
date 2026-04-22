# Agent bundle config.yaml

Every [custom agent bundle](../develop/custom-agent.md) under `agents/<name>/` includes a `config.yaml` that overrides per-agent paths and model choices. It's how one repo hosts multiple specialised agents (personal assistant, dog agent, …) with different personalities, RAG docs, and LLM providers.

## Beginner mental model

- One YAML file per agent bundle.
- Loaded by the agent's `from_bundle()` classmethod at startup.
- Most fields are **optional** — anything unset falls back to the root [`settings.json`](config-json.md).
- Edit the file, restart the agent, changes take effect.

## Inspect it now

```bash
cat agents/personal_assistant/config.yaml
cat agents/dog_agent/config.yaml
```

## Example

```yaml
# agents/personal_assistant/config.yaml
data_dir: core/data
rag_dir: rag_docs
rag_namespace: personal_assistant_knowledge

model: gpt-4o
max_tokens: 16000
```

```yaml
# agents/dog_agent/config.yaml
data_dir: agents/dog_agent/data/
rag_dir: rag_docs
rag_namespace: dog_agent_knowledge

max_tokens: 16000
llm_provider: byteplus
```

## Fields

| Field | Default | Purpose |
|---|---|---|
| `data_dir` | `agent_file_system/` | Per-agent file system root — overrides the shared [AGENT_FILE_SYSTEM_PATH](../concepts/agent-file-system.md) |
| `rag_dir` | *(none)* | Subdir of the bundle holding RAG docs. Indexed into memory at startup |
| `rag_namespace` | bundle name | Namespace for the ChromaDB collection — keeps per-agent vectors isolated |
| `llm_provider` | from `settings.json` → `model.llm_provider` | Override LLM provider for this agent |
| `model` | from `settings.json` → `model.llm_model` | Model name override (e.g. `gpt-4o`, `claude-sonnet-4-6`) |
| `max_tokens` | provider default | Max tokens per response |

## Where paths are resolved

Relative paths resolve against the bundle's own directory, not the project root:

| In `config.yaml` | Resolves to |
|---|---|
| `data_dir: core/data` | `<repo>/core/data` (if project-relative override is intended) |
| `rag_dir: rag_docs` | `<bundle>/rag_docs/` |
| `data_dir: agents/dog_agent/data/` | `<repo>/agents/dog_agent/data/` (absolute-from-root) |

`personal_assistant` uses project-root-relative; `dog_agent` spells out the full path. Both work.

## RAG docs layout

When `rag_dir` is set, the bundle ships its own corpus:

```
agents/personal_assistant/
├── agent.py            # The subclass
├── config.yaml         # This file
├── rag_docs/           # Indexed into memory namespace
│   ├── calendar_conventions.md
│   ├── email_templates.md
│   └── ...
└── rag_docs_taskdocs/  # Optional: task-example docs
```

Memory indexes `rag_docs/` into a **separate namespace** (`rag_namespace`) so it doesn't mix with the shared `agent_file_system/` memory.

## Precedence

```
settings.json (root)
    ↓
config.yaml (bundle)        ← overrides provider, model, data paths
    ↓
runtime agent instance      ← uses final values
```

Environment variables still apply on top (API keys, OAuth credentials) — they're read by the provider clients regardless of bundle.

## Loading

Agents are loaded via their `from_bundle()` classmethod:

```python
from agents.personal_assistant.agent import PersonalAssistantAgent

agent = PersonalAssistantAgent.from_bundle(
    bundle_path=Path("agents/personal_assistant"),
)
```

The method reads `config.yaml`, sets up data/rag dirs, instantiates the LLM interface with the right provider, and returns the agent.

## Related

- [Custom agent](../develop/custom-agent.md) — full walkthrough on building your own bundle
- [settings.json](config-json.md) — the root-level fallback
- [LLM providers](../providers/llm.md) — valid `llm_provider` values
- [Memory](../concepts/memory.md) — how `rag_dir` gets indexed
