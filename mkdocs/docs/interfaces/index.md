# Interfaces

CraftBot has four user-facing interfaces and an internal UI layer that unifies them. Pick based on your environment: browser for the best UX, TUI for terminal work, CLI for scripting, GUI for desktop automation.

<div class="grid cards" markdown>

- :material-web:{ .lg .middle } __[Browser](browser.md)__

    ---

    Modern web UI (default). Requires Node.js 18+.

- :material-console:{ .lg .middle } __[CLI](cli.md)__

    ---

    Lightweight command-line interface. No dependencies.

- :material-monitor:{ .lg .middle } __[TUI](tui.md)__

    ---

    Rich terminal UI powered by Textual. No Node.js needed.

- :material-desktop-classic:{ .lg .middle } __[GUI / Vision](gui-vision.md)__

    ---

    Desktop automation via vision models. Experimental.

- :material-layers-outline:{ .lg .middle } __[UI layer](ui-layer.md)__

    ---

    The adapter layer that lets one agent drive all four interfaces.

- :material-pulse:{ .lg .middle } __[Living UI](living-ui.md)__

    ---

    Dynamic UI state binding between agent and adapter.

</div>

## Which interface should I use?

| You want | Use |
|---|---|
| The best out-of-the-box experience | [Browser](browser.md) |
| A terminal-native UI | [TUI](tui.md) |
| Scripting, piping, minimal footprint | [CLI](cli.md) |
| Desktop automation (move mouse, click, screenshot) | [GUI](gui-vision.md) |

Launch examples are on each page and on the [interfaces overview](../commands/index.md).

## Related

- [Commands](../commands/index.md) — the slash commands available in every interface
- [Service mode](../start/service-mode.md) — run the browser interface as a background daemon
