# Custom agent

CraftBot ships an extensible `AgentBase` class. Subclass it, add a personality, bundle your own RAG docs and custom actions, and you have a specialized agent. The `agents/personal_assistant/` and `agents/dog_agent/` bundles are working references.

## What you're building

An agent bundle — a directory under `agents/<your-agent>/` containing:

- `agent.py` — subclass of `AgentBase` with `_generate_role_info_prompt()` override
- `config.yaml` — per-agent settings (model, provider, RAG dir)
- `data/` — private [agent file system](../concepts/agent-file-system.md) with this agent's AGENT.md, USER.md, etc.
- *(optional)* `rag_docs/` — domain docs indexed into a private memory namespace
- *(optional)* `data/action/` — actions scoped to this agent

## Step 1 — Scaffold the bundle

```bash
mkdir -p agents/research_agent/{data,rag_docs}
touch agents/research_agent/{__init__.py,agent.py,config.yaml}
```

Directory layout:

```
agents/research_agent/
├── __init__.py
├── agent.py
├── config.yaml
├── data/                    # Agent file system (AGENT.md, USER.md, …)
│   └── action/              # Optional: per-agent actions
└── rag_docs/                # Optional: RAG corpus
```

## Step 2 — Write `config.yaml`

```yaml
# agents/research_agent/config.yaml
data_dir: agents/research_agent/data
rag_dir: rag_docs
rag_namespace: research_agent_knowledge

llm_provider: anthropic
model: claude-sonnet-4-6
max_tokens: 16000
```

All fields are optional — unset ones fall back to [`settings.json`](../configuration/agent-config-yaml.md).

## Step 3 — Subclass `AgentBase`

```python
# agents/research_agent/agent.py
from __future__ import annotations
from pathlib import Path
import yaml

from app.agent_base import AgentBase


class ResearchAgent(AgentBase):
    """An agent specialized in literature review and synthesis."""

    @classmethod
    def from_bundle(cls, bundle_dir: str | Path) -> "ResearchAgent":
        bundle_path = Path(bundle_dir).resolve()
        cfg = yaml.safe_load((bundle_path / "config.yaml").read_text())
        return cls(cfg, bundle_path)

    def __init__(self, cfg: dict, bundle_path: Path):
        self._bundle_path = Path(bundle_path)
        self._cfg = cfg
        super().__init__(
            data_dir=cfg.get("data_dir", "app/data"),
            chroma_path=str(self._bundle_path / cfg.get("rag_dir", "rag_docs")),
            llm_provider=cfg.get("llm_provider", "anthropic"),
        )

    def _generate_role_info_prompt(self) -> str:
        return (
            "You are a research agent specialized in synthesis across academic papers, "
            "industry reports, and primary sources. Always cite sources. When uncertain, "
            "say so and recommend further reading. Use the agent file system to keep "
            "notes across sessions."
        )
```

## Step 4 — Register in `run.py` (or call directly)

The simplest path is to call `from_bundle` in your own entry point:

```python
# run_research.py
import asyncio
from agents.research_agent.agent import ResearchAgent

async def main():
    agent = ResearchAgent.from_bundle("agents/research_agent")
    await agent.start()

asyncio.run(main())
```

Or patch `run.py` to dispatch to your agent based on a CLI flag:

```bash
python run.py --agent research_agent
```

## Step 5 — Test

Send a message:

> *"Find recent papers on prompt caching strategies for LLMs and summarise."*

Watch the agent pull from your RAG corpus, cite sources, and save notes to your private `data/MEMORY.md`.

## Overridable hooks

`AgentBase` exposes several `_prefixed_` hooks your subclass can override:

| Hook | Purpose |
|---|---|
| `_generate_role_info_prompt()` | Fills `AGENT_ROLE_PROMPT` — your agent's persona + instructions |
| `_load_extra_system_prompt()` | Append extra static text to the system prompt |
| `_register_extra_actions()` | Register additional actions programmatically |
| `_build_db_interface()` | Point at a different database backend |
| `_get_interface_capabilities_prompt()` | Interface-aware prompt fragment (e.g. "You're in browser mode, so you can receive attachments.") |

The `agents/dog_agent/` in the repo is a minimal working example — override `_generate_role_info_prompt` to replace all English with "woof".

## Per-agent actions

Drop `.py` files under `agents/<agent>/data/action/` — they're discovered just like core actions but only registered when this agent runs.

```
agents/research_agent/data/action/citation_format.py   # @action(...)
```

## Per-agent skills

Set `selected_skills` in [`config.yaml`](../configuration/agent-config-yaml.md) to preload skills for every task created by this agent.

## Per-agent RAG

`rag_dir: rag_docs` tells memory to index `agents/<agent>/rag_docs/` into its own ChromaDB namespace (`rag_namespace`). Your agent can `memory_search("...")` and get hits only from its private corpus.

## Load order

When your agent starts:

1. Read `config.yaml`
2. Initialize `AgentBase` with overrides from the config
3. Discover core actions (`app/data/action/*.py`)
4. Discover bundle actions (`agents/<agent>/data/action/*.py`) — can override core
5. Load MCP servers from `mcp_config.json`
6. Build memory index: `agent_file_system/` PLUS `agents/<agent>/rag_docs/`
7. Register the agent's role prompt
8. Start the [agent loop](../concepts/agent-loop.md)

## Related

- [Agent bundle config.yaml](../configuration/agent-config-yaml.md)
- [Agent loop](../concepts/agent-loop.md) — what you're subclassing
- [Custom action](custom-action.md) — for bundling per-agent actions
- [Skills overview](skills/index.md) — for bundling strategy into prompts
