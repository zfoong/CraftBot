# Browser mode

CraftBot's default interface — a modern web UI served from a local Node.js dev server, with live [event stream](../concepts/event-stream.md) rendering, rich chat, task visualization, and a full settings surface.

## Quick start

```bash
python run.py
```

Opens `http://localhost:xxxx` in your default browser automatically.

## Requirements

- Python **3.10+**.
- **Node.js 18+** (installed separately — see [Install](../start/install.md)).
- An [LLM API key](../providers/llm.md).

No Node.js? Use [TUI mode](tui.md) — `python run.py --tui`.

## Features

- **Live action cards** — every action renders as a card with inputs/outputs.
- **Streaming chat** — responses stream token-by-token.
- **Task tree** — see [todos](../concepts/task-session.md), status, and ETA.
- **Integration setup** — click-through OAuth flows.
- **Skill marketplace** — browse, install, toggle.
- **MCP manager** — add/edit/remove MCP servers with live validation.
- **Multi-task view** — watch multiple running tasks side by side.

## Running as a service

For an always-on assistant that survives terminal close:

```bash
python service.py install
```

See [Service mode](../start/service-mode.md) for the full runbook.

## Remote access

By default the browser binds to `localhost` only. To access from another machine, see [Service mode](../start/service-mode.md) — SSH tunnel and Tailscale are both supported.

## Layout

- [`app/browser/interface.py`](../concepts/logs.md) — Python backend
- [`app/ui_layer/browser/`](../concepts/logs.md) — WebSocket bridge, frontend handshake
- Frontend lives in a separate Node.js subproject (Next.js-style), launched by `run.py`

## Knobs

```json
// settings.json (partial)
{ "general": { "agent_name": "CraftBot" } }
```

The agent name appears in the browser title bar and header.

## Theming

Coal + orange palette matches the TUI and documentation. Custom themes go in the frontend subproject — see [Living UI](living-ui.md) for the state-sync layer that powers them.

## Related

- [TUI](tui.md) — terminal alternative (no Node.js)
- [UI layer](ui-layer.md) — the shared adapter layer
- [Living UI](living-ui.md) — dynamic state sync
- [Service mode](../start/service-mode.md) — run it as a daemon
