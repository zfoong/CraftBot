# Commands

Commands are slash-prefixed inputs (`/help`, `/cred status`, `/skill list`) that the UI intercepts before they reach the agent. They're how you configure connections, inspect state, and control the interface without writing a task.

<div class="grid cards" markdown>

- :material-book-alphabet:{ .lg .middle } __[Built-in commands](builtin.md)__

    ---

    Reference for every `/command` bundled with CraftBot.

- :material-console-line:{ .lg .middle } __[CLI-anything](cli-anything.md)__

    ---

    Have the agent run any shell command via the `run_shell` action.

</div>

## How commands work

Commands are registered in the UI layer at startup. When you type `/foo ...`, the UI routes it to the matching command handler instead of the agent. Unrecognized `/` prefixes fall through to the agent as a regular message.

See [UI layer](../interfaces/ui-layer.md) for how commands are dispatched and [Custom command](../develop/custom-action.md) for how to add your own.

## Related

- [Interfaces](../interfaces/index.md) — where you type commands
- [Connections](../connections/index.md) — uses commands like `/google login` extensively
