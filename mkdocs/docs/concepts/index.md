# Concepts

The core building blocks of CraftBot. Start here if you want a mental model of how the agent thinks, acts, and remembers — before touching config.

Every page on this section opens with a one-sentence definition and a "mental model" beat you can hold in your head, then shows a command you can run *right now* to see the concept in action.

<div class="grid cards" markdown>

- :material-sync:{ .lg .middle } __[Agent loop](agent-loop.md)__

    ---

    The main cycle: react → select action → execute → observe.

- :material-flash-outline:{ .lg .middle } __[Triggers](trigger.md)__

    ---

    What starts a task — user messages, schedules, external events.

- :material-identifier:{ .lg .middle } __[Task sessions](task-session.md)__

    ---

    The unit of work. Each task has its own state, todos, and event stream.

- :material-broadcast:{ .lg .middle } __[Event stream](event-stream.md)__

    ---

    Pub/sub for task progress. Drives the UI and lets you observe what the agent is doing.

- :material-lightning-bolt-outline:{ .lg .middle } __[Actions](action.md)__

    ---

    The things the agent can do. Library of ~80+ built-in actions; custom actions easy to add.

- :material-bullseye-arrow:{ .lg .middle } __[Skill & action selection](skill-selection.md)__

    ---

    How the agent picks the right action for each step.

- :material-format-quote-open-outline:{ .lg .middle } __[Prompts](prompt.md)__

    ---

    Prompt templates and the registry that lets you override them.

- :material-view-column-outline:{ .lg .middle } __[Context engine](context-engine.md)__

    ---

    Assembles the full prompt — system, history, task state, memory — with KV caching.

- :material-database-search-outline:{ .lg .middle } __[Memory](memory.md)__

    ---

    RAG memory over ChromaDB. Auto-indexed events, semantic recall.

- :material-folder-multiple-outline:{ .lg .middle } __[Agent file system](agent-file-system.md)__

    ---

    The agent's persistent markdown knowledge base: AGENT.md, USER.md, MEMORY.md, and more.

- :material-file-document-multiple-outline:{ .lg .middle } __[Logs](logs.md)__

    ---

    What gets logged, where, and how to configure verbosity.

</div>

## Further reading

- [Task modes](../modes/index.md) — how the agent loop varies by task type
- [Develop](../develop/index.md) — build your own actions, skills, and agents
- [Configuration](../configuration/index.md) — where every knob lives
