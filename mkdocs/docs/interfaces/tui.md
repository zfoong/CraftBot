# TUI mode

A rich terminal interface built on [Textual](https://textual.textualize.io/). No Node.js required — just Python. Gets you a full-screen UI with panels, live action streams, scrollable history, and interactive settings.

## Quick start

```bash
python run.py --tui
```

## Features

- **Live action panel** — watch every [action](../concepts/action.md) fire as the agent works.
- **Chat panel** — conversation transcript, updated live.
- **Task panel** — active [task](../concepts/task-session.md) with todos and status.
- **Settings tabs** — integrations, MCP, skills, credentials, models (all the [slash commands](../commands/builtin.md), but with forms).
- **Keyboard-first** — every action has a keybinding.

## Requirements

- Python **3.10+**.
- An [LLM API key](../providers/llm.md).
- No Node.js.
- Textual (installed automatically by `python install.py`).

## Layout

- [`app/tui/interface.py`](../concepts/logs.md) — main TUI adapter
- [`app/tui/app.py`](../concepts/logs.md) — Textual app definition
- [`app/tui/widgets.py`](../concepts/logs.md) — custom widgets
- [`app/tui/styles.py`](../concepts/logs.md) — TCSS theme
- [`app/tui/onboarding/`](../start/onboarding.md) — first-run wizard

## Settings panels

The TUI surfaces five settings panels that match the [`/menu`](../commands/builtin.md) command groups:

| Panel | Matches command | File |
|---|---|---|
| Credentials | `/cred status` | [`credential_commands.py`](../concepts/logs.md) |
| Integrations | `/integrations` | [`integration_settings.py`](../concepts/logs.md) |
| MCP servers | `/mcp list` | [`mcp_settings.py`](../concepts/logs.md) |
| Skills | `/skill list` | [`skill_settings.py`](../concepts/logs.md) |
| General settings | `/menu` | [`settings.py`](../concepts/logs.md) |

## Keyboard shortcuts

| Key | Action |
|---|---|
| `Ctrl+C` | Quit (clean shutdown) |
| `Ctrl+L` | Clear view |
| `Tab` | Focus next panel |
| `Shift+Tab` | Focus previous panel |
| `↑` / `↓` in input | Command history |
| `F1` | Help |

Full list: press `F1` inside the TUI.

## Theme

Coal + orange to match the rest of the CraftBot brand. Edit [`app/tui/styles.py`](../concepts/logs.md) to theme it yourself.

## When to use TUI over browser

| Use TUI when | Use [Browser](browser.md) when |
|---|---|
| No Node.js available | You want the richest UI |
| SSH / remote shell | Local or tunneled to localhost |
| You prefer keyboard | You prefer mouse + rich widgets |
| Resource-constrained | Desktop with browser handy |

## Related

- [CLI](cli.md) — even lighter weight
- [Browser](browser.md) — richer alternative (needs Node.js)
- [UI layer](ui-layer.md) — the shared adapter layer
- [Onboarding](../start/onboarding.md) — first-run wizard
