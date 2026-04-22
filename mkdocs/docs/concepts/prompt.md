# Prompts

Prompts are the text templates CraftBot sends to the LLM. They're where the agent's *voice* lives — how it reasons about actions, how it talks about itself, what policies it follows. Every prompt is registered in a central registry so you can override any of them without forking the codebase.

## Beginner mental model

- A **prompt** is a named template string with `{placeholders}`.
- The **prompt registry** stores every built-in prompt by name.
- The **context engine** pulls prompts from the registry, fills placeholders, and assembles the final LLM input.
- You can **override** any prompt by registering a new version with the same name — the registry uses last-write-wins.

Prompts are text — they don't execute code. They're how you shape behaviour without writing Python.

## Inspect it now

List every registered prompt from Python:

```python
from app.prompt import prompt_registry
for name in prompt_registry.list_names():
    print(name)
```

## The prompt families

| Family | Prompts | Used by |
|---|---|---|
| **Event stream** | `EVENT_STREAM_SUMMARIZATION_PROMPT` | [Event stream](event-stream.md) rollup |
| **Action selection** | `SELECT_ACTION_PROMPT`, `SELECT_ACTION_IN_TASK_PROMPT`, `SELECT_ACTION_IN_SIMPLE_TASK_PROMPT`, `SELECT_ACTION_IN_GUI_PROMPT` | [Action router](skill-selection.md) |
| **Context** | `AGENT_ROLE_PROMPT`, `AGENT_INFO_PROMPT`, `POLICY_PROMPT`, `USER_PROFILE_PROMPT`, `ENVIRONMENTAL_CONTEXT_PROMPT`, `AGENT_FILE_SYSTEM_CONTEXT_PROMPT` | [Context engine](context-engine.md) system-prompt assembly |
| **Routing** | `ROUTE_TO_SESSION_PROMPT` | [Trigger queue](trigger.md) — match incoming triggers to sessions |
| **GUI** | `GUI_REASONING_PROMPT`, `GUI_REASONING_PROMPT_OMNIPARSER`, `GUI_QUERY_FOCUSED_PROMPT`, `GUI_PIXEL_POSITION_PROMPT`, `GUI_ACTION_SPACE_PROMPT` | [GUI / Vision mode](../interfaces/gui-vision.md) |
| **Skill selection** | `SKILLS_AND_ACTION_SETS_SELECTION_PROMPT`, `SKILL_SELECTION_PROMPT`, `ACTION_SET_SELECTION_PROMPT` | Task creation — picks skills + action sets |

All of them are `import`-able from `app.prompt` for reading or overriding.

## The registry

```python
from app.prompt import register_prompt, get_prompt

# Read the current version
current = get_prompt("SELECT_ACTION_PROMPT")

# Override it
register_prompt(
    "SELECT_ACTION_PROMPT",
    """Your custom prompt here with {placeholders}...""",
)
```

Overrides take effect immediately — no restart needed. The registry is shared across the whole agent.

## Assembly: system prompt vs user prompt

Every LLM call uses two pieces:

- **System prompt** — built once per call by the [context engine](context-engine.md), concatenating: `AGENT_ROLE_PROMPT`, `AGENT_INFO_PROMPT`, `POLICY_PROMPT`, `USER_PROFILE_PROMPT`, `ENVIRONMENTAL_CONTEXT_PROMPT`, `AGENT_FILE_SYSTEM_CONTEXT_PROMPT`. This part is KV-cached across calls.
- **User prompt** — the specific question: `SELECT_ACTION_PROMPT` + event stream snapshot + the trigger's `next_action_description`. This part changes every call.

Splitting the boundary this way lets the provider cache the system half (see [Context engine](context-engine.md)), cutting cost and latency dramatically.

## Placeholders

Each prompt declares its own `{placeholders}`. Common ones:

| Placeholder | Filled with |
|---|---|
| `{agent_name}` | From `general.agent_name` in [settings.json](../configuration/config-json.md) |
| `{user_profile}` | From `agent_file_system/USER.md` |
| `{current_task}` | The running [task](task-session.md)'s `instruction` + todos |
| `{event_stream}` | Output of [`EventStream.to_prompt_snapshot()`](event-stream.md) |
| `{available_actions}` | Compiled from the task's `action_sets` |
| `{selected_skills}` | Skill instructions injected from `selected_skills` |
| `{os_language}` | Detected OS language code |

## Prompt overrides for custom agents

A subclassed agent (see [Custom agent](../develop/custom-agent.md)) typically overrides just two prompts:

- `AGENT_ROLE_PROMPT` — the persona ("You are a no-nonsense research assistant specializing in …")
- `POLICY_PROMPT` — the rules ("Never execute actions that modify X without user approval …")

Example:

```python
# agents/my_agent/agent.py
class MyAgent(AgentBase):
    def _load_extra_system_prompt(self) -> str:
        return "You speak like a 1920s detective. Be terse."
```

## Related

- [Context engine](context-engine.md) — the consumer of the prompt registry
- [Skill & action selection](skill-selection.md) — four action-selection prompt variants
- [Event stream](event-stream.md) — uses `EVENT_STREAM_SUMMARIZATION_PROMPT`
- [Custom agent](../develop/custom-agent.md) — the usual place to override prompts
