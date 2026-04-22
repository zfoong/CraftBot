# Triggers

A trigger is the unit of input that wakes the agent up — a small record saying *"react to this, at this time, with this context"*. Every reaction — user messages, schedules, memory processing, proactive heartbeats, waiting-for-reply timeouts — starts as a trigger on the priority queue.

## Beginner mental model

- The agent **sleeps** on an async queue.
- Anything that should cause a reaction — a typed message, a cron tick, an incoming Slack DM, a scheduled planner — is wrapped in a `Trigger` and dropped onto the queue.
- The queue is a **priority heap**: the trigger with the nearest `fire_at` timestamp and highest priority (lowest number) wins.
- One trigger in → one iteration of the [agent loop](agent-loop.md) out.

Triggers can be scheduled in the future (`fire_at` later than now). They sleep in the queue until their time comes.

## Inspect it now

Set the log level to DEBUG and watch the queue:

```bash
tail -f logs/*.log | grep -E "TRIGGER|PUT|GET"
```

## Example output

```text
[PUT] Incoming trigger for session=None (skip_merge=False)
[TRIGGER QUEUE] BEFORE PUT
(empty)
[PUT] No existing session trigger → pushing normally
[TRIGGER QUEUE] AFTER PUT
1. session_id=None | prio=10 | fire_at=1713745328.85 | delta=0.00s
   desc=what's the weather in Tokyo

[GET] CALLED
[TRIGGER FIRED] session=None | desc=what's the weather in Tokyo
```

## Anatomy

A trigger is a small dataclass:

| Field | Type | Purpose |
|---|---|---|
| `fire_at` | float (unix timestamp) | When the trigger is eligible to run |
| `priority` | int | Ordering within a `fire_at` tie. Lower = higher priority |
| `next_action_description` | str | Human-readable hint used when routing/merging |
| `payload` | dict | Arbitrary context carried to the workflow |
| `session_id` | str \| None | Which task/session this trigger belongs to |
| `waiting_for_reply` | bool | True if the trigger is a wait-for-user timeout |

`payload["type"]` is the single most important field. It tells [`react()`](agent-loop.md#routing-rules) which workflow to run:

| `payload["type"]` | Workflow |
|---|---|
| `"memory_processing"` | Memory distillation |
| `"proactive_heartbeat"` | Proactive due-task sweep |
| `"proactive_planner"` | Daily / weekly / monthly planner |
| `"task_execution"` / `"scheduled"` / *(unset)* | Regular conversation / task flow |

## The queue: put / get / fire

**`put(trigger)`** — insert a trigger. If another trigger already exists for the same `session_id`, the **newer trigger replaces** the older ones (prefer-newest). If no `session_id` is set, the queue asks the LLM to route the trigger to an existing session or open a new one. System triggers (`memory_processing`, `task_execution`, `scheduled`) skip LLM routing.

**`get()`** — block until a trigger's `fire_at` has arrived. Multiple ready triggers for the same session are **merged**: their descriptions are concatenated (deduped), payloads are merged, and the highest-priority `fire_at` wins.

**`fire(session_id, message=..., platform=...)`** — bring an existing trigger's `fire_at` forward to *now*. Used when a user replies while their task is waiting. If a message is passed, it's attached to the trigger's payload as `pending_user_message` and picked up by `react()` so the LLM sees it.

## LLM-based session routing

When `put()` receives a trigger with no `session_id` and there are running tasks, it prompts the LLM with:

- a list of running sessions (task name, instruction, todo progress, recent events, platform, conversation id),
- the recent conversation history (last 10 events),
- the incoming trigger's description,

and asks: "does this trigger belong to one of these sessions, or is it new?" The response is JSON — either `{"action": "route", "session_id": "..."}` or `{"action": "new"}`. The prompt template is [`ROUTE_TO_SESSION_PROMPT`](prompt.md) and is configurable.

## Merging active triggers

If two triggers land on the same session while one is already being processed, the queue tracks them in the `_active` dict and the second one's payload gets folded into the first. This is how a user message mid-task gets surfaced to the LLM without a race condition — `pop_pending_user_message(session_id)` extracts the queued message when the next iteration runs.

## Creating triggers

Components create triggers by calling `self.triggers.put(Trigger(...))`:

- **User message** → priority 10, `fire_at=now`, session via LLM routing
- **Scheduled task** → priority 50, `fire_at=<scheduled time>`, `payload.type="scheduled"`
- **Proactive heartbeat** → priority 50, `fire_at=<cron tick>`, `payload.type="proactive_heartbeat"`
- **Wait-for-reply** → priority 100, `fire_at=<now + 3 hours>`, `waiting_for_reply=True`
- **External chat event** (Slack/Discord/Telegram) → priority 10, `fire_at=now`, `payload.platform="<platform>"`, `payload.contact_id`, `payload.channel_id`

Custom triggers are how you integrate CraftBot with anything outside the box — see [Custom action](../develop/custom-action.md) and [MCP servers](../connections/mcp.md).

## Related

- [Agent loop](agent-loop.md) — the consumer of triggers
- [Event stream](event-stream.md) — what runs *during* a trigger
- [Proactive](../modes/proactive.md) — the largest source of scheduled triggers
- [Prompts](prompt.md) — the `ROUTE_TO_SESSION_PROMPT` template
