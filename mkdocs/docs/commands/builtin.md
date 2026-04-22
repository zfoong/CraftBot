# Built-in commands

Every slash command shipped with CraftBot. Type them in any [interface](../interfaces/index.md) — the [UI layer](../interfaces/ui-layer.md) intercepts them before they hit the agent.

## Quick start

```
/help                  # list every command
/help cred             # detailed help for one command
```

## Command catalogue

| Command | What it does |
|---|---|
| `/help [name]` | Show command help. No arg = list all. |
| `/menu` | Open the settings menu (models, integrations, skills, MCP). |
| `/cred status` | Show all active credentials. |
| `/cred list` | Same as `status`, terse. |
| `/cred integrations` | Show all integrations grouped by platform. |
| `/cred <provider> connect` | Start connect flow for one provider (Google, Slack, …). |
| `/integrations` | Open the integrations panel. |
| `/provider [name]` | Switch LLM provider (`anthropic`, `openai`, `google`, `byteplus`, `remote`). |
| `/skill list` | List all skills and their enabled state. |
| `/skill enable <name>` | Enable a skill. |
| `/skill disable <name>` | Disable a skill. |
| `/skill_invoke <name>` | Invoke a skill directly. |
| `/mcp list` | List configured MCP servers. |
| `/mcp add` | Add an MCP server (interactive). |
| `/mcp remove <name>` | Remove an MCP server. |
| `/reset` | Reset the current session (clear task + events). |
| `/clear` | Clear the UI view (does not affect state). |
| `/update` | Check for CraftBot updates. |
| `/exit` | Shut down the agent cleanly. |
| `/agent_command <cmd>` | Send an agent-internal command (diagnostic). |

## Per-connection commands

Each [external integration](../connections/index.md) ships its own set. Examples:

```
/google login
/slack invite
/telegram login-bot <token>
/discord logout
/notion status
```

See the relevant [connection page](../connections/index.md) for the full list per integration.

## Dispatch model

Command routing happens in three steps:

1. UI intercepts input starting with `/`.
2. `CommandRegistry.resolve(name)` returns the handler.
3. Handler runs with parsed args; output displays in the UI.

Unrecognized `/` prefixes fall through to the agent as a regular message.

## Registering your own

```python
from app.ui_layer.commands.registry import register_command

@register_command(name="greet", description="Say hello")
async def greet(args: list[str]) -> str:
    return f"Hello {args[0] if args else 'world'}"
```

Appears as `/greet` on next launch. See [Custom command](../develop/custom-action.md) for full walkthrough (shares the patterns of custom actions).

## Related

- [Commands overview](index.md)
- [CLI-anything](cli-anything.md) — the `run_shell` escape hatch
- [UI layer](../interfaces/ui-layer.md) — where dispatch happens
- [Credentials](../connections/credentials.md) — the `/cred` family
