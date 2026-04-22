# CLI mode

The lightest interface CraftBot ships. No Node.js, no Textual, no browser — just stdin, stdout, and the [UI layer](ui-layer.md). Best for scripting, piping, SSH sessions, and CI.

## Quick start

```bash
python run.py --cli
```

## Features

- Line-by-line I/O.
- All [slash commands](../commands/builtin.md) work.
- Streaming output for [action events](../concepts/event-stream.md).
- ANSI color via the built-in `formatter`.
- Pipe-friendly — redirect `stdin` / `stdout` for automation.

## Non-interactive mode

You can drive CLI mode with a script:

```bash
echo "what is 2+2" | python run.py --cli
```

Output goes to stdout; logs still go to [`logs/`](../concepts/logs.md).

## Requirements

- Python **3.10+**.
- An [LLM API key](../providers/llm.md).
- No Node.js.
- No Textual / rich — just stdlib.

## Layout

The CLI interface lives in:

- [`app/cli/interface.py`](../concepts/logs.md) — `CLIInterface` adapter
- [`app/cli/formatter.py`](../concepts/logs.md) — ANSI color + pretty-print
- [`app/cli/onboarding.py`](../start/onboarding.md) — first-run wizard

## When to use CLI over TUI

| Use CLI when | Use [TUI](tui.md) when |
|---|---|
| Scripting / automation | You want a live view of actions |
| SSH with minimal setup | Interactive rich UI is OK |
| Piping to another tool | You need status bars / panels |
| CI test runs | You're iterating locally |

## Knobs

```json
// settings.json
{ "general": { "os_language": "en" } }
```

CLI formatter respects `os_language` for greetings and help text.

## Related

- [TUI](tui.md) — richer terminal alternative
- [UI layer](ui-layer.md) — the adapter layer
- [Built-in commands](../commands/builtin.md) — same commands work here
- [Interfaces overview](index.md)
