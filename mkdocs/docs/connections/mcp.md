# MCP servers

The [Model Context Protocol](https://modelcontextprotocol.io/) is an open standard for exposing tools (actions) from external processes. Plug an MCP server into CraftBot, and every tool it exposes becomes a native [action](../concepts/action.md) the agent can call — with the same router, same prompts, same events.

## The core idea

- **Any program** that speaks MCP over stdio, WebSocket, or SSE can be a tool provider.
- **CraftBot's MCP adapter** ([`MCPActionAdapter`](../concepts/action.md)) wraps each MCP tool as a CraftBot action at load time.
- **Tools appear in the registry** alongside built-ins — the router treats them identically.

## Scenarios

### 1) Local filesystem / SQLite / shell MCP

Use community-built MCPs for filesystem access, database queries, shell execution. Configure in `mcp_config.json`, start the agent, the tools become available.

### 2) Remote SaaS via MCP bridge

Some SaaS providers expose MCP endpoints (e.g. Sentry, Linear). Configure with `transport: "sse"` or `transport: "websocket"` pointing at their endpoint.

### 3) Your own MCP server

Write a small program that implements the MCP spec; plug it in. Useful for exposing internal APIs or proprietary data to the agent without touching CraftBot's code.

## Command flow

```
                ┌────────────────────────────┐
                │  app/config/mcp_config.json │  (hot-reloadable)
                └──────────┬──────────────────┘
                           ↓
                ┌──────────────────────┐
                │  MCPClient per server │
                └──────────┬────────────┘
                           ↓ connects via stdio/ws/sse
                ┌──────────────────────┐
                │  MCPActionAdapter     │  wraps tools as actions
                └──────────┬────────────┘
                           ↓
                ┌──────────────────────┐
                │  Action registry      │
                └──────────┬────────────┘
                           ↓
                Agent router picks + executes
```

## Configuration

`app/config/mcp_config.json`:

```json
{
  "mcp_servers": [
    {
      "name": "filesystem",
      "description": "Read/write files on the local machine",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"],
      "env": {},
      "enabled": true
    },
    {
      "name": "sentry",
      "description": "Query Sentry issues",
      "transport": "sse",
      "url": "https://sentry.example.com/mcp/sse",
      "headers": { "Authorization": "Bearer <token>" },
      "enabled": true
    }
  ]
}
```

Fields:

| Field | Values |
|---|---|
| `name` | Unique identifier. Becomes the tool prefix. |
| `description` | Shown in `/mcp list` |
| `transport` | `stdio` / `websocket` / `sse` |
| `command` + `args` + `env` | For `stdio` transport — how to launch the server |
| `url` + `headers` | For `websocket` / `sse` transports |
| `enabled` | Master switch per server |

Hot-reloaded — no restart needed after editing.

## Managing servers via command

```
/mcp list                    # show configured servers
/mcp add                     # interactive add
/mcp remove <name>           # remove
/mcp enable <name>           # toggle on
/mcp disable <name>          # toggle off
```

## Tool naming

MCP tools are prefixed with the server name to avoid collisions:

```
filesystem:read_file
filesystem:write_file
sentry:list_issues
```

The router sees them as normal action names.

## Credential precedence for MCP

Same as other [credentials](credentials.md):

1. **Environment variables** referenced in `env: {...}` (stdio) or `headers: {...}` (SSE/WS).
2. **Literal strings** in `mcp_config.json` (not recommended for secrets).
3. *(nothing)* — tool calls fail at runtime.

Prefer `env: { "API_TOKEN": "" }` and set `API_TOKEN` in `.env` — keeps secrets out of config.

## Security rules

- **Stdio transport** runs the command with the user's privileges. Audit the server binary before enabling.
- **Remote transports** (WebSocket, SSE) may send your prompts and data to the remote. Review what the server does before trusting it.
- **Disabled servers** don't connect — use `enabled: false` to pin a config without running the server.
- Keep the config file out of public repos if it references private endpoints.

## Adding MCP servers from the agent

Because `mcp_config.json` is hot-reloaded, the agent itself can add MCP servers when it hits a capability gap. From [`AGENT.md`](../concepts/agent-file-system.md):

> When you CANNOT complete a task due to missing capabilities:
> 1. IDENTIFY — What capability is missing?
> 2. SEARCH — `web_search` for MCP servers
> 3. INSTALL — edit `mcp_config.json`
> 4. WAIT — hot-reload detects the change
> 5. CONTINUE — proceed with the new tool

Approve these edits before they run if the server requires credentials.

## Related

- [Actions](../concepts/action.md) — how MCP tools become actions
- [Skill & action selection](../concepts/skill-selection.md) — how they get picked
- [Credentials](credentials.md) — how auth is handled
- [Custom action](../develop/custom-action.md) — the native alternative
