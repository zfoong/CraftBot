# Context engine

The context engine is the piece that **assembles the prompt** sent to the LLM for every call. It takes the static agent identity, the user profile, the environment, the agent file system, the live task, and the event stream, and stitches them into a `(system_prompt, user_prompt)` pair with a carefully designed cache boundary.

## Beginner mental model

- Every LLM call needs two pieces: a **system prompt** (who you are, rules, policies) and a **user prompt** (what to do, with current state).
- The engine builds the system prompt once per call from **static** pieces that rarely change (agent identity, policy, user profile, environment).
- The user prompt has a **static template** followed by dynamic content (event stream, memory hits, query) followed by output format.
- The split between static and dynamic is deliberate: everything *before* the dynamic content can be **KV-cached** by the LLM provider, turning subsequent calls into a cheap incremental append.

Cache well → 10× faster follow-up calls. Don't cache → pay full price every time.

## Inspect it now

Dump the next system prompt:

```python
from agent_core import ContextEngineRegistry
engine = ContextEngineRegistry.get()
print(engine.build_system_prompt())
```

## System-prompt ingredients

Assembled in this fixed order (each from a named prompt in the [registry](prompt.md)):

| # | Prompt | Source |
|---|---|---|
| 1 | `AGENT_ROLE_PROMPT` | Subclass-overridable persona |
| 2 | `AGENT_INFO_PROMPT` + `SOUL_PROMPT` | [`AGENT.md`](agent-file-system.md) + [`SOUL.md`](agent-file-system.md) |
| 3 | `AGENT_FILE_SYSTEM_CONTEXT_PROMPT` | File list, schemas, what each `.md` does |
| 4 | `USER_PROFILE_PROMPT` | [`USER.md`](agent-file-system.md) |
| 5 | `POLICY_PROMPT` | Safety/approval rules, language instructions |
| 6 | `ENVIRONMENTAL_CONTEXT_PROMPT` | OS, timezone, current time, detected language |

This whole block is **static for the duration of a session**. Providers that support prompt caching (Anthropic, Gemini, BytePlus) cache it after the first call — subsequent calls only pay for the user-prompt half.

## User-prompt ingredients

| Part | Content |
|---|---|
| Template | `SELECT_ACTION_*_PROMPT` for the current workflow (see [Skill & action selection](skill-selection.md)) |
| Static block | Available actions list, task instructions, selected skills |
| Dynamic block | Event stream snapshot (via [`to_prompt_snapshot()`](event-stream.md)), memory hits, current query |
| Output format | JSON schema the LLM must match |

Keeping the static block *before* the dynamic block lets providers cache through the template-plus-actions portion — only the last ~N events and the query change call-to-call.

## KV caching strategy

CraftBot uses two levels of cache:

1. **Prefix cache** — the system prompt. Applied by the provider automatically when the call reuses a cached prefix. Free after the first paid call.
2. **Session cache** — per-workflow. The engine tracks which events have been synced to the provider cache via [`mark_session_synced()`](event-stream.md#session-cache-delta-tracking). Subsequent calls send only **delta events** via `get_delta_events()`, letting the cache grow incrementally.

If the event stream summarizes (token threshold hit), the session cache is invalidated for all workflows — events past the sync point no longer exist.

## Hooks

The engine exposes three optional hooks for runtimes that need extra context:

| Hook | Used for |
|---|---|
| `get_conversation_history_hook` | Enterprise chat-server runtime (WCA) |
| `get_chat_target_info_hook` | Enterprise chat-server runtime (WCA) |
| `get_user_info_hook` | Enterprise chat-server runtime (WCA) |

CraftBot default: unset (returns empty string).

## Message source block

When a message arrives from an external platform (Slack, Telegram, etc.), the engine injects a small XML block telling the LLM *who* is talking:

```xml
<message_source>
  <platform>Slack</platform>
  <contact_name>Bob</contact_name>
  <channel_name>#engineering</channel_name>
</message_source>
```

This lets the agent address replies correctly when multiple platforms route to the same task.

## Memory retrieval

Before each LLM call, the engine asks [memory](memory.md) for the top-K relevant pointers for the current query:

```python
memory_context = context_engine.get_memory_context(query)
```

The result is a compact list of `[file_path] section_path — summary` pointers. The agent then calls `read_file` to pull the full content only if it needs to — this keeps context small while retaining recall.

## Knobs

Most tuning lives in [`settings.json`](../configuration/config-json.md) (memory enabled, model provider, etc.). Deeper customization — cache tier, memory top-K, custom prompt injection — is in the engine constructor and best changed via [Custom agent](../develop/custom-agent.md).

## Related

- [Prompts](prompt.md) — the components being assembled
- [Event stream](event-stream.md) — the dynamic half of the user prompt
- [Memory](memory.md) — how retrieval feeds the engine
- [LLM providers](../providers/llm.md) — which providers support prefix caching
