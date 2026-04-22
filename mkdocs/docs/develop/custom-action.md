# Custom action

Actions are Python functions with a schema. One file, one `@action` decorator, and the agent can call your code.

## What you're building

A function the [action router](../concepts/skill-selection.md) can pick, with:

- A **name** the LLM will reference
- A **description** that teaches the LLM *when* to pick it
- **Input schema** (JSON schema lite) for parameters
- **Output schema** for the return dict
- An optional **test_payload** for local dry-runs

## Step 1 — Drop a file in `app/data/action/`

```bash
touch app/data/action/check_weather.py
```

Any `.py` under `app/data/action/` is auto-discovered on startup.

## Step 2 — Write the action

```python
# app/data/action/check_weather.py
from app.action.action_framework.registry import action
import urllib.request
import json

@action(
    name="check_weather",
    description=(
        "Return current weather for a city. "
        "Use when the user asks about weather, temperature, or outdoor conditions."
    ),
    mode="ALL",                          # CLI | GUI | ALL
    execution_mode="internal",           # internal (in-process) | sandboxed
    action_sets=["core"],                # appears in the core set
    platforms=["linux", "windows", "darwin"],
    input_schema={
        "city": {
            "type": "string",
            "example": "Tokyo",
            "description": "City name to look up",
        },
    },
    output_schema={
        "status":      {"type": "string",  "example": "success"},
        "temperature": {"type": "number",  "example": 22.5},
        "conditions":  {"type": "string",  "example": "partly cloudy"},
    },
    test_payload={"city": "Tokyo"},
)
def check_weather(input_data: dict) -> dict:
    city = input_data["city"]
    url = f"https://wttr.in/{city}?format=j1"
    with urllib.request.urlopen(url, timeout=5) as r:
        data = json.loads(r.read())
    c = data["current_condition"][0]
    return {
        "status": "success",
        "temperature": float(c["temp_C"]),
        "conditions": c["weatherDesc"][0]["value"],
    }
```

## Step 3 — Register with the right action set

`action_sets: ["core"]` makes it available to every task. Scope it more narrowly:

| Action set | Contains |
|---|---|
| `core` | Always available — use sparingly |
| `web_research` | Only tasks that select `web_research` |
| `file_operations` | File I/O tasks |
| `shell` | Shell-capable tasks |
| `document_processing` | PDF / DOCX |
| Custom set name | Create your own — tasks will opt in via `task_start` |

## Step 4 — Reload

Stop the agent (`/exit`) and restart. On startup, the registry auto-discovers the new file. Actions aren't hot-reloaded — adding/removing requires restart.

```
[REGISTRY] Loaded 87 actions from app/data/action/
```

## Step 5 — Test

### From the agent

Ask the agent to use it:

> *"What's the weather in Tokyo?"*

The router should pick `check_weather` and you'll see `action_start: check_weather` in logs.

### From Python

```python
from app.action.action_framework.registry import registry_instance
fn = registry_instance.get_action("check_weather")
print(fn({"city": "Tokyo"}))
```

### From CLI (dry-run)

If you supplied `test_payload`, the agent's diagnostic CLI can dry-run:

```
python -m app.diagnostic.run_action check_weather
```

## Metadata reference

| Field | Required | Purpose |
|---|---|---|
| `name` | yes | Action id the LLM uses |
| `description` | yes | **Teaches the LLM when to use** — be specific |
| `mode` | no (default `ALL`) | `CLI` / `GUI` / `ALL` visibility |
| `execution_mode` | no (default `internal`) | `internal` runs in-process; `sandboxed` runs in a subprocess |
| `action_sets` | yes | List of sets — how tasks scope to you |
| `platforms` | no | List of OS families; omit = all |
| `default` | no | If `True`, available even without explicit set selection |
| `input_schema` | yes | JSON-schema-lite per input param |
| `output_schema` | yes | JSON-schema-lite for the return dict |
| `test_payload` | no | Example input for dry-run testing |

## Load order / precedence

1. Core built-ins (`app/data/action/*.py`)
2. [MCP tools](../connections/mcp.md) (prefixed with server name)
3. [Skill-provided tools](skills/craftbot-skill.md)
4. [Agent bundle actions](custom-agent.md) (e.g. `agents/dog_agent/data/action/`)

**Higher = overridable by lower.** An agent bundle can override a core action by registering with the same `name`.

## Writing good descriptions

The **description** is what the LLM sees in the candidate list. It's the single most important field for getting your action picked correctly.

Good:

> *"Return current weather for a city. Use when the user asks about weather, temperature, or outdoor conditions. Returns temperature in Celsius and a conditions string."*

Bad:

> *"Gets weather"*

Include: what it does, **when** to use it, **what it returns**.

## Related

- [Actions concept](../concepts/action.md)
- [Skill & action selection](../concepts/skill-selection.md)
- [Actions catalogue](../reference/actions.md) — browse built-ins for examples
- [Custom agent](custom-agent.md) — actions scoped to an agent bundle
- [MCP servers](../connections/mcp.md) — the external alternative
