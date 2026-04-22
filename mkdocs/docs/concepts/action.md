# Actions

An **action** is one thing the agent can do — send a message, read a file, query a database, post a Slack reply, run a shell command. The agent's entire vocabulary lives in the action library: if there's no action for something, the agent can't do it. *(Unless you give it the [`run_shell`](../commands/cli-anything.md) action — then it can do anything.)*

## Beginner mental model

- An **action** is a named function with a JSON schema for its inputs and outputs.
- The **action library** is the registry of all built-in actions — ~80+ of them, from `send_message` to `memory_search` to `send_gmail`.
- The **action router** is the LLM-driven picker: given a user query, it selects one or more actions and fills in their inputs.
- **Action sets** group actions for [task](task-session.md) scoping — a task declares `"action_sets": ["file_operations", "web_research"]`, and only those actions are available during execution.

An action run produces events on the [stream](event-stream.md): `action_start: <name>` → `action_end: <name> -> ok (extras)`.

## Inspect it now

List all actions:

```bash
/cred integrations     # shows all integration actions grouped by platform
```

Or in Python, via the registry:

```python
from agent_core import registry_instance
for name in registry_instance._registry:
    print(name)
```

## Anatomy

Every action has:

```python
@register_action(
    name="send_gmail",
    description="Send an email via Gmail.",
    action_sets=["core"],                # which sets contain it
    platforms=[PLATFORM_ALL],            # linux / darwin / windows / all
    visibility_mode="CLI",               # CLI / GUI / ALL
    input_schema={
        "to":      {"type": "string", "required": True},
        "subject": {"type": "string", "required": True},
        "body":    {"type": "string", "required": True},
    },
    output_schema={
        "status":     {"type": "string"},
        "message_id": {"type": "string"},
    },
    default=True,                        # included even without explicit set selection
)
async def send_gmail(to: str, subject: str, body: str) -> dict:
    ...
```

The metadata is what the router sees — it never reads the implementation. The `description` is the single most important field; it's what the LLM uses to decide *when* to pick this action.

## The seven action sets

Default set names — actions can belong to multiple:

| Set | Contains |
|---|---|
| `core` | `send_message`, `task_start`, `task_update_todos`, `task_complete`, set management — always available |
| `file_operations` | `read_file`, `write_file`, `edit_file`, `grep_files`, `stream_read`, list/search |
| `web_research` | `web_search`, `fetch_url`, `scrape_page` |
| `document_processing` | PDF/DOCX read/write, conversion |
| `clipboard` | `clipboard_read`, `clipboard_write` |
| `shell` | `run_shell`, `python_exec` |
| `gui_interaction` | `mouse_click`, `keyboard_input`, `screenshot` (only when GUI mode on) |

Integrations (Discord, Slack, Google, …) contribute additional actions that are enabled automatically once the integration is connected. See [Connections overview](../connections/index.md).

## Selection

The [action router](skill-selection.md) picks actions via one of four prompts depending on the current workflow:

| Workflow | Prompt |
|---|---|
| Conversation | `SELECT_ACTION_PROMPT` |
| Simple task | `SELECT_ACTION_IN_SIMPLE_TASK_PROMPT` |
| Complex task | `SELECT_ACTION_IN_TASK_PROMPT` |
| GUI task | `SELECT_ACTION_IN_GUI_PROMPT` |

All four are overridable via the [prompt registry](prompt.md).

## Execution

Once picked, actions flow through a four-step beat (see [Agent loop](agent-loop.md#the-action-beat)):

1. **`_retrieve_and_prepare_actions`** — resolve the action by name, bind inputs, wire `parent_id` so downstream events link back
2. **`_execute_actions`** — run the action (sync or async), catch exceptions
3. **Event logging** — `action_start` + `action_end` events are added to the stream
4. **Output** — the action's return dict flows back to the workflow, which may feed into the next iteration

Multiple actions can run **in parallel** within one iteration if the router returns multiple decisions.

## Platform dispatch

An action can have per-platform implementations. `run_shell` has three variants: `shell_exec` (shared default), `shell_exec_windows`, `shell_exec_darwin`. When the registry looks up an action, it picks the platform-specific implementation first, falling back to `PLATFORM_ALL`. This is how CraftBot does "run on macOS with zsh, Windows with cmd, Linux with bash" from one logical action name.

## Adding your own

See [Custom action](../develop/custom-action.md) — one file, `@register_action` decorator, done. Your action appears in the registry on the next agent start.

## Related

- [Skill & action selection](skill-selection.md) — how the router chooses
- [CLI-anything](../commands/cli-anything.md) — the `run_shell` escape hatch
- [Actions catalogue](../reference/actions.md) — every built-in action
- [Custom action](../develop/custom-action.md) — write your own
- [Skills](../develop/skills/index.md) — bundling multiple actions into a capability
