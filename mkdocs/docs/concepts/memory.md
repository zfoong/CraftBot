# Memory

CraftBot's memory is a **RAG system over the [agent file system](agent-file-system.md)**. It chunks every markdown file into semantic sections, embeds them in [ChromaDB](https://www.trychroma.com/), and returns **pointers** (not content) when the agent searches. Short-term events accumulate in `EVENT_UNPROCESSED.md`, get distilled daily into `MEMORY.md`, and become part of the searchable corpus.

## Beginner mental model

Memory has three moving parts:

- **Live stream** — events stack into `EVENT_UNPROCESSED.md` as the agent works.
- **Distillation** — once a day (default hour `3` AM), a memory-processing task reads `EVENT_UNPROCESSED.md`, scores each event, writes important ones to `MEMORY.md`, and clears the unprocessed file.
- **Retrieval** — the [context engine](context-engine.md) asks memory for the top-K *pointers* relevant to the current query. Pointers are lightweight (`file_path`, `section_path`, `summary`), so the agent can decide whether to pull the full content with `read_file`.

Memory never returns raw content. It returns **"where to look."** This is the key design choice — it keeps the context window small while preserving recall across long-running agents.

## Inspect it now

Search memory from the agent:

```
/memory_search authentication redirect URI
```

Or from Python:

```python
from agent_core import MemoryManager
manager = MemoryManager()  # or retrieve from registry
pointers = manager.retrieve("authentication redirect URI", top_k=5)
for p in pointers:
    print(p)
```

## Example output

```text
[USER.md] ## Identity - Email: ... Location: Tokyo, Timezone: JST
[MEMORY.md] ### Auth migration (2026-04-10) - Migrated OAuth redirect URIs from localhost:8080 to localhost:8765
[AGENT.md] ## Self-Improvement Protocol - Search MCP servers when capability is missing
```

## Anatomy of a chunk

```python
@dataclass
class MemoryChunk:
    chunk_id: str          # UUID
    file_path: str         # Relative to agent_file_system/
    section_path: str      # "## Header > ### Sub-header"
    title: str             # Last header in path
    content: str           # Full section content
    summary: str           # First ~150 chars — what the pointer shows
    content_hash: str      # For change detection
    file_modified_at: str
    indexed_at: str
```

Chunks are semantic — one per markdown header. A file with 5 sections becomes 5 chunks, each independently retrievable.

## Indexing

Memory auto-indexes every markdown file under `agent_file_system/` plus user-supplied RAG docs under `agents/<agent>/rag_docs/`. Indexing is **incremental**:

- On startup, the `MemoryFileWatcher` scans for files newer than their last-indexed timestamp.
- Only changed sections are re-embedded. Unchanged chunks keep their existing vectors.
- File deletions remove their chunks from the store.

Vectors live in `chroma_db_memory/` by default.

## Daily distillation

A scheduled trigger fires at [`MEMORY_PROCESSING_SCHEDULE_HOUR`](../configuration/config-json.md#constants-not-in-json) (default `3` AM local). The resulting memory-processing task uses the [`memory-processor` skill](../develop/skills/craftbot-skill.md) and runs this loop:

1. Read `EVENT_UNPROCESSED.md` for the day's events
2. For each event, score its importance for long-term recall
3. Use `memory_search` to detect duplicates
4. Write important, unique events to `MEMORY.md` as new sections
5. Clear `EVENT_UNPROCESSED.md`

See [Special workflows](../modes/special-workflows.md) for the workflow that runs this task.

## The memory_search action

The agent itself has a `memory_search` action available in every task. Its inputs are a query string and `top_k`; its output is a list of pointers. Typical pattern:

```
1. memory_search("budget Q3")     →  3 pointers
2. read_file("MEMORY.md", ...)     →  full section of the best hit
3. act on the retrieved info
```

## Master switch

```json
// settings.json
{ "memory": { "enabled": true } }
```

When disabled:

- Memory-processing triggers are logged and skipped.
- `memory_search` returns empty.
- The context engine's memory retrieval returns an empty string — the agent falls back to working from the event stream only.

## Startup processing

By default, `PROCESS_MEMORY_AT_STARTUP` is `False` — the agent does not re-process the previous session's events on launch. Flip it to `True` in `app/config.py` if you want every startup to distill yesterday's events immediately.

## Privacy

Memory is **local**. ChromaDB runs embedded. Embeddings are computed locally (ChromaDB's built-in) unless a custom embedding provider is configured. No memory content leaves the machine.

## Related

- [Agent file system](agent-file-system.md) — the corpus being indexed
- [Context engine](context-engine.md) — the consumer of memory retrieval
- [Event stream](event-stream.md) — the live "before it becomes memory" buffer
- [Special workflows](../modes/special-workflows.md) — where the daily distillation runs
- [Custom agent](../develop/custom-agent.md) — how to add your own RAG docs via `rag_dir` in `config.yaml`
