# Event stream

The event stream is the per-session narrative of everything that happened during a task: actions started, actions finished, messages sent, errors caught. It's what the UI renders, what the LLM sees as history, and what gets summarized into memory.

## Beginner mental model

Think of it as **append-only logbook per [task session](task-session.md)**, with an automatic summarizer:

- Every event is a `kind`, a `message`, and a `severity` (DEBUG / INFO / WARN / ERROR).
- Events accumulate in `tail_events` — recent, full-fidelity.
- When the token count crosses a threshold, the oldest events get **rolled up** into a textual `head_summary` by the LLM.
- The agent reads the stream via `to_prompt_snapshot()` which returns `head_summary + recent tail events`.

One stream per session. Streams are created lazily when a task starts and cleared when it ends.

## Inspect it now

Every interface renders the stream live. In the [TUI](../interfaces/tui.md) it fills the main pane. In logs, filter for event lines:

```bash
tail -f logs/*.log | grep -E "action_start|action_end|EventStream"
```

## Example

```text
[EventStream] Triggering summarization: 31204 tokens >= 30000 threshold
[EventStream] Running synchronous summarization (31204 tokens)
[EventStream] Summarization complete. Tokens: 9845
```

A compact event in `to_prompt_snapshot()` format looks like:

```text
Recent Event:
[2026-04-22 10:14:02] action_start: send_gmail
[2026-04-22 10:14:04] action_end: send_gmail -> ok (message_id=18a2f3e)
[2026-04-22 10:14:04] action_start: memory_search
[2026-04-22 10:14:06] action_end: memory_search -> ok (hits=3)
```

## What gets logged

The agent logs four main kinds, plus anything you add:

| Kind | When |
|---|---|
| `action_start` | An action has been selected and is about to run |
| `action_end` | The action finished; message includes `status` and extras |
| `user_message` | A user message arrives (local or routed from Slack, Discord, etc.) |
| `agent_message` | The agent sends a reply |

Custom event kinds are fine — any string is accepted.

## Summarization

Auto-summarization kicks in when `_total_tokens >= summarize_at_tokens` (default **30,000**). The oldest events are packaged with the current `head_summary` (if any) and sent to the LLM via `EVENT_STREAM_SUMMARIZATION_PROMPT`. The LLM returns a new summary that replaces the old one; the summarized events are dropped. The tail is truncated so that the remaining events total ≤ `tail_keep_after_summarize_tokens` (default **10,000**).

If the LLM is in a consecutive-failure state, summarization falls back to **prune-without-summary** — oldest events are simply dropped so the tail stays under the threshold. This prevents retry storms during provider outages.

## Tunable thresholds

Default thresholds live in the `EventStream` constructor:

```python
EventStream(
    llm=...,
    summarize_at_tokens=30000,
    tail_keep_after_summarize_tokens=10000,
)
```

Raise `summarize_at_tokens` for longer live history (costs more tokens per call). Lower `tail_keep_after_summarize_tokens` for more aggressive compaction. To override per-agent, pass custom values when the stream is created, or subclass the agent (see [Custom agent](../develop/custom-agent.md)).

!!! warning "Relationship constraint"
    `tail_keep_after_summarize_tokens + 2000` must be less than `summarize_at_tokens`. If you set it too high, the stream clamps it to `summarize_at_tokens - 2000` and logs a warning.

## Long message externalization

Any single event message longer than **200,000 chars** is written to a temp file instead of living in the stream. The event becomes a pointer:

```text
Action grep_files completed. The output is too long therefore is saved in
/tmp/event_grep_files_20260422_101432123.txt to save token.
| keywords: user, authentication, redirect
| To retrieve the content, agent MUST use the 'grep_files' action ...
```

The agent learns to read the pointer file via `stream_read` or `grep` when it needs the full content. This keeps context windows sane on actions that return huge outputs.

## Session cache delta tracking

When CraftBot uses session-level prompt caching (see [Context engine](context-engine.md)), only *new* events since the last sync need to be sent to the cache. The stream keeps per-call-type sync points (`_session_sync_points`) and `get_delta_events(call_type)` returns only events appended after the last sync. If summarization has occurred between syncs, the cache is invalidated and re-populated from scratch.

## Severity

Every event has a severity (`DEBUG`, `INFO`, `WARN`, `ERROR`, default `INFO`). The UI can filter by severity; logs can too. Severity doesn't affect summarization — the LLM summarizer sees everything.

## Clearing a stream

`EventStream.clear()` wipes `head_summary`, `tail_events`, token count, and sync points. Used when a session id is reused for a new task, so no stale context leaks between runs.

## Related

- [Agent loop](agent-loop.md) — the producer
- [Task sessions](task-session.md) — one stream per session
- [Context engine](context-engine.md) — how the stream is injected into prompts
- [Memory](memory.md) — where summarized events end up long-term
- [Event types reference](../reference/events.md) — full `kind` catalogue
