# Living UI

!!! note "Limited source access"
    Living UI ships as compiled bytecode (`.pyc`) only — public `.py` source isn't currently accessible for this page. The documentation below is from observable behaviour and integration points. If you're extending it, reach out to [@zfoong](https://github.com/zfoong) for the source.

The Living UI is CraftBot's **dynamic state-sync layer** — it keeps the UI in lockstep with the agent across reconnects, tab switches, and multi-task scenarios. Without it, browser mode would need to re-fetch everything on every reload; with it, the UI stays live even while the agent is mid-action.

## Beginner mental model

- A **persistent reactive state** that survives UI reconnects (e.g. browser refresh).
- Binds the agent's running state — current task, active events, pending approvals — to whatever adapter is rendering.
- Observable via integration hooks in [`app/data/action/`](../concepts/action.md) and [`app/ui_layer/settings/`](ui-layer.md) where adjacent `living_ui_*.pyc` files live.

## Integration surface

The living UI exposes its behaviour to the rest of the code through two compiled modules:

- `app/ui_layer/settings/living_ui_settings.pyc` — settings panel for living-UI behaviour (enable, reconnect timeout, diffing strategy)
- `app/data/action/living_ui_actions.pyc` — actions the agent can call to update living-UI state (e.g. request approval, show a popup)

## What it binds

| Surface | Living UI role |
|---|---|
| Chat transcript | Diffed on reconnect — only new messages transferred |
| Active task + todos | Kept in sync across browser tabs |
| Action cards | Persist state across UI restarts |
| Pending approvals | Re-surface after reconnect |
| Settings dirty-state | Unsaved changes preserved |

## Enabling

Enabled by default in browser mode. Not used in CLI (stateless) or TUI (state is in-process). Configurable via the `living_ui_settings` module.

## When to disable

- You're running in an environment without a persistent WebSocket (e.g. serverless).
- You want minimum memory footprint (state store adds modest overhead).
- You're debugging a UI freeze and suspect living UI is the cause.

## Related

- [UI layer](ui-layer.md) — the parent architecture
- [Browser](browser.md) — primary consumer
- [Event stream](../concepts/event-stream.md) — the data source for diffs
