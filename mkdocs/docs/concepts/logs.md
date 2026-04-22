# Logs

Every CraftBot run writes a timestamped log file to `logs/` at the project root. Logs are the first thing to read when something goes wrong — they capture trigger routing, action calls, LLM errors, summarization events, and connection flows.

## Beginner mental model

- CraftBot uses **Loguru**.
- Each run creates a **fresh log file** at `logs/<YYYYMMDDhhmmss>.log` — tail this, not the console.
- Logs **rotate at 50 MB** and are kept for **14 days**.
- The **console is muted by default** — to see logs while running, tail the file.

## Inspect it now

Find the latest log and tail it:

```bash
tail -f logs/*.log
```

Filter for what you need:

```bash
tail -f logs/*.log | grep -E "\[REACT\]|\[WORKFLOW|ERROR"
```

## Log location

- Directory: `logs/` at the project root.
- Format: `<YYYYMMDDhhmmss>.log` (no prefix), or `<name>_<timestamp>.log` when a custom name is passed.
- Rotation: automatic at 50 MB. Older files kept for 14 days.

## Severity & format

Default severity: **DEBUG** for the file sink, **ERROR** for the (currently muted) console. Loguru format preserves tracebacks and local variables via `backtrace=True`, `diagnose=True`.

Key log-line prefixes to know:

| Prefix | Emitter |
|---|---|
| `[REACT]` | [Agent loop](agent-loop.md) entering a reaction |
| `[WORKFLOW: ...]` | Which workflow handled the trigger |
| `[STATE]` | Session / current-task state snapshots |
| `[PUT]` / `[GET]` / `[FIRE]` / `[TRIGGER QUEUE]` | [Trigger queue](trigger.md) operations |
| `[EventStream]` | Summarization and stream lifecycle |
| `[MEMORY]` | Memory processing and retrieval |
| `[PROACTIVE]` | Proactive heartbeat / planner |
| `[TaskManager]` | Task persistence / recovery |
| `[LLM]` | LLM provider calls and errors |
| `[OAuth]` / `[Credentials]` | Integration auth flows |

## Configuring log level

The logger is initialized with defaults at startup (via `define_log_level()`), but subclassed agents can customize:

```python
from app.logger import define_log_level

logger = define_log_level(
    print_level="INFO",   # console threshold (currently muted by default)
    logfile_level="DEBUG",
    name="my_agent",       # filename prefix
)
```

## Enabling the console sink

The console output is commented out in `app/logger.py` by default. To see logs live in your terminal, uncomment the `_logger.add(sys.stderr, ...)` block and restart.

## What doesn't go to logs

- **LLM prompts and responses** — too large; check the [event stream](event-stream.md) for these.
- **User messages** — tracked in [agent_file_system/EVENT.md](agent-file-system.md) and in the event stream, not logs.
- **Secrets** — API keys and tokens are masked before logging. If you see one appear in logs, it's a bug; please report it.

## Retention

Default retention is 14 days. Change by re-initializing:

```python
_logger.add(log_path, rotation="100 MB", retention="30 days", ...)
```

## Related

- [Troubleshooting](../troubleshooting/index.md) — symptom → log-line patterns
- [Event stream](event-stream.md) — the agent's per-task narrative (distinct from logs)
- [Configuration](../configuration/index.md) — where `logs/` lives among other paths
