# UI layer

The UI layer is the **abstraction between the agent and the interface**. It's how one agent can drive [CLI](cli.md), [TUI](tui.md), [browser](browser.md), and [GUI](gui-vision.md) modes without the agent knowing which one is active.

## Beginner mental model

Three pieces:

- **`UIController`** — central orchestrator. Knows about the agent, the running task, and the active interface.
- **`InterfaceAdapter`** (abstract) — one per interface. Renders chat, shows actions, displays the task panel, etc.
- **`EventBus` + `UIStateStore`** — the reactive layer. Events flow from agent → UIController → adapter; state changes flow the other way.

Swap the adapter, get a different interface. Every other layer stays identical.

## Quick start

```
python run.py          # Browser adapter
python run.py --tui    # TUI adapter
python run.py --cli    # CLI adapter
```

`run.py` picks the right `InterfaceAdapter` and hands it to `UIController`.

## Layout

```
app/ui_layer/
├── controller/ui_controller.py    # UIController — the orchestrator
├── adapters/
│   ├── base.py                     # InterfaceAdapter — abstract protocol
│   ├── cli_adapter.py              # CLI-specific rendering
│   ├── tui_adapter.py              # Textual widgets
│   └── browser_adapter.py          # WebSocket bridge
├── components/protocols.py         # ChatComponentProtocol, ActionPanelProtocol, …
├── events/event_bus.py             # Pub/sub for UI updates
├── state/store.py                  # Reactive state store
├── commands/                       # Slash-command registry + builtin commands
│   ├── base.py
│   ├── executor.py
│   ├── registry.py
│   └── builtin/                    # /help, /cred, /skill, /mcp, …
├── settings/                        # Settings panel handlers
├── onboarding/                      # First-run wizard shared code
├── themes/                          # Cross-adapter theming
├── metrics/                         # Usage / performance metrics
└── local_llm_setup.py               # Helper for Ollama setup flow
```

## Component protocols

Adapters implement a fixed set of component protocols:

| Protocol | Renders |
|---|---|
| `ChatComponentProtocol` | Chat transcript, user + agent messages |
| `ActionPanelProtocol` | Live action cards (start / running / done) |
| `TaskComponentProtocol` | Active task summary + todos |
| `SettingsPanelProtocol` | Integrations / skills / MCP / models tabs |
| `OnboardingProtocol` | First-run wizard |
| `CommandInputProtocol` | The input box with slash-command handling |

Each protocol is an abstract base; each adapter fills them in differently (ANSI strings for CLI, Textual widgets for TUI, WebSocket messages for browser).

## Events

The UI layer bridges three directions:

```
Agent / event stream  →  EventBus  →  Adapter components  (render)
Adapter UI events     →  EventBus  →  UIController         (intent)
Settings changes      →  UIStateStore                       (reactive)
```

Events are typed — `chat.message`, `action.start`, `action.end`, `task.updated`, `todo.transition`. Adding a new event is a one-liner in the bus and a handler per adapter.

## Commands

Slash-command dispatch (see [Built-in commands](../commands/builtin.md)) lives here because it's interface-agnostic. The `CommandRegistry` is populated at startup by importing every file in `commands/builtin/`. Third-party commands register by calling `register_command(...)`.

## State store

`UIStateStore` tracks things like:

- Current theme
- Active settings panel
- Agent status (idle / running / error)
- Pending approval prompts

It's reactive — adapters subscribe and re-render on change.

## Adding a new interface

See the "UI layer" section of [Custom agent](../develop/custom-agent.md) for a walkthrough. TL;DR:

1. Subclass `InterfaceAdapter`.
2. Implement each component protocol.
3. Register your adapter in `run.py`'s dispatcher.
4. Add a CLI flag to `run.py`.

## Related

- [CLI](cli.md), [TUI](tui.md), [Browser](browser.md), [GUI](gui-vision.md) — the four adapters
- [Living UI](living-ui.md) — the reactive layer under the state store
- [Commands](../commands/index.md) — dispatch lives here
- [Event stream](../concepts/event-stream.md) — the source of render events
