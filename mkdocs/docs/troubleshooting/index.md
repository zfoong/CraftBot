# Troubleshooting

First, check [`logs/`](../concepts/logs.md) — most problems leave a trail there.

<div class="grid cards" markdown>

- :material-alert-circle-outline:{ .lg .middle } __[Runtime issues](runtime.md)__

    ---

    Install failures, missing Node.js, CUDA errors, Playwright hiccups.

- :material-link-off:{ .lg .middle } __[Connection issues](connections.md)__

    ---

    OAuth refresh failures, expired tokens, webhook mismatches.

- :material-brain:{ .lg .middle } __[Provider issues](providers.md)__

    ---

    Rate limits, model errors, context-window overruns.

</div>

## Quick checks

| Symptom | Check |
|---|---|
| Agent hangs after "Thinking…" | [Provider issues](providers.md) — rate limit or API outage |
| `/google login` opens browser but returns error | [Connection issues](connections.md) — OAuth redirect URI mismatch |
| Agent says "I don't have that capability" | `/skill list` — skill may not be enabled |
| Running out of memory or context | [Provider issues](providers.md) — check context window |
| Browser mode shows blank page | [Runtime issues](runtime.md) — Node.js missing or wrong version |

## Related

- [Logs](../concepts/logs.md)
- [Getting started](../start/index.md)
