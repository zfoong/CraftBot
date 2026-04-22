# CLI-anything

CraftBot ships with a single action called **`run_shell`** that gives the agent access to the host shell. With it, the agent can do *anything* the command line can do — install software, run build steps, query your database, poke APIs with `curl`, start a dev server, whatever.

## Beginner mental model

- One action. One schema. Universal power.
- The agent calls it like any other action: name + inputs (command, shell, timeout, cwd, env, background).
- It runs on the **host OS**'s native shell: `cmd` on Windows, `zsh` on macOS, `bash` on Linux.
- Long-running processes (dev servers, watchers) must set `background: true`, or the task blocks.

`run_shell` is in the **`core`** action set, so it's available to every task by default. Disable by removing it from `core` if you want a sandboxed agent.

## Inspect it now

Ask the agent to run something trivial:

> *run `echo hello` in my shell*

```text
[ACTION] run_shell -> ok (stdout="hello\n", return_code=0)
```

## Input schema

```json
{
  "command":    "git status",
  "shell":      "auto",                 // or "bash" / "zsh" / "cmd" / explicit
  "timeout":    60,                     // seconds; exceed = terminate
  "cwd":        "/home/user/my-repo",
  "env":        { "DEBUG": "1" },
  "background": false
}
```

## Output schema

```json
{
  "status":      "success",             // or "timeout" / "error"
  "stdout":      "...",
  "stderr":      "",
  "return_code": 0,
  "message":     "Timed out after 60s.",  // only on timeout/error
  "pid":         12345                     // only when background=true
}
```

## Platform dispatch

Three implementations live under the hood:

- `shell_exec` (shared) — default
- `shell_exec_windows` — Windows-specific (uses `cmd`)
- `shell_exec_darwin` — macOS-specific (uses `zsh`)

The [action registry](../concepts/action.md#platform-dispatch) picks the right implementation based on `platform.system()`. The agent calls the logical name `run_shell` and gets the correct behavior.

## Background processes

For long-running things:

```json
{
  "command": "npm run dev",
  "background": true,
  "cwd": "/home/user/my-app"
}
```

Returns `pid` immediately. The agent can then `curl localhost:3000` or read logs to verify the server is up. To stop the process later, the agent uses `kill <pid>` or `taskkill /PID <pid>`.

## Timeouts

Default `timeout: 60` seconds. If exceeded, the process is terminated and `status: "timeout"` is returned. Set a larger timeout for slow operations (Docker builds, large installs) up to a reasonable ceiling.

## Security considerations

Giving an LLM shell access is powerful and risky. CraftBot's defaults:

- **No sandbox** — `run_shell` runs with the user's privileges.
- **No confirmation** — the agent can run it without user approval.
- **Logged** — every shell command appears in the [event stream](../concepts/event-stream.md) and [logs](../concepts/logs.md).

!!! warning "Review what the agent runs"
    If you're running CraftBot on a production machine, consider:

    - Removing `run_shell` from the `core` set (custom agent).
    - Running the agent in a container.
    - Adding approval tiers via a wrapper action.

## Why not just "shell execution" as a feature?

Because framing it as an **action** keeps everything uniform:

- Appears in the [action router](../concepts/skill-selection.md) alongside `send_gmail` and `web_search`.
- Emits `action_start` / `action_end` [events](../concepts/event-stream.md) like anything else.
- Can be removed or restricted with the same mechanism as any other action (action sets, visibility mode).

## Related

- [Actions](../concepts/action.md) — the primitive `run_shell` is an instance of
- [Commands overview](index.md) — slash commands (different layer)
- [Built-in commands](builtin.md) — UI-layer commands
- [Custom action](../develop/custom-action.md) — build your own action
