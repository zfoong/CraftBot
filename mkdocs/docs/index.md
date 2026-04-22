---
hide:
  - navigation
  - toc
---

# CraftBot

Your personal AI assistant — lives inside your machine, works for you 24/7. CraftBot autonomously interprets tasks, plans actions, and executes them across the browser, filesystem, connected services, and the shell.

<div class="grid cards" markdown>

- :material-rocket-launch-outline:{ .lg .middle } __Get started__

    ---

    Install CraftBot, run the onboarding wizard, and send your first task in under 5 minutes.

    [:octicons-arrow-right-24: Install](start/install.md) ·
    [Quickstart](start/quickstart.md)

- :material-lightbulb-on-outline:{ .lg .middle } __Concepts__

    ---

    Learn the mental model: agent loop, triggers, actions, memory, context, skills.

    [:octicons-arrow-right-24: Concepts](concepts/index.md)

- :material-hammer-wrench:{ .lg .middle } __Extend CraftBot__

    ---

    Build custom skills, actions, and subclassed agents. Plug in MCP servers.

    [:octicons-arrow-right-24: Develop](develop/index.md)

</div>

## What CraftBot does

<div class="grid cards" markdown>

- :material-brain:{ .lg .middle } __Reasons & plans__

    ---

    Breaks down complex tasks into todos, picks the right action at each step, and iterates until done.

- :material-database-outline:{ .lg .middle } __Remembers__

    ---

    RAG-based memory with ChromaDB. Distills events at midnight and recalls them when relevant.

- :material-connection:{ .lg .middle } __Connects__

    ---

    13 external services — Discord, Slack, Telegram, Notion, Google Workspace, LinkedIn, Zoom, WhatsApp, and more.

- :material-puzzle-outline:{ .lg .middle } __Extensible__

    ---

    Skills, custom actions, MCP servers, and subclassable agents. Build your own CraftBot.

- :material-bell-ring-outline:{ .lg .middle } __Proactive__

    ---

    Learns your preferences and goals. Proposes tasks, reminds you, schedules follow-ups (with approval).

- :material-monitor-dashboard:{ .lg .middle } __Runs anywhere__

    ---

    Browser, TUI, CLI, or desktop GUI mode. Cross-platform (Windows, Linux, macOS). Service-mode background daemon.

</div>

## Start here

<div class="grid cards" markdown>

- [Getting started :octicons-arrow-right-24:](start/index.md) — install, onboard, first task
- [Task modes :octicons-arrow-right-24:](modes/index.md) — simple, complex, special, proactive
- [Interfaces :octicons-arrow-right-24:](interfaces/index.md) — browser, TUI, CLI, GUI
- [Connections :octicons-arrow-right-24:](connections/index.md) — connect Discord, Slack, Google, …
- [Configuration :octicons-arrow-right-24:](configuration/index.md) — config.json, env vars
- [Troubleshooting :octicons-arrow-right-24:](troubleshooting/index.md) — when things go wrong

</div>

## Project status

!!! warning "GUI mode is experimental"
    GUI mode is still being hardened — expect issues when the agent switches to vision-based desktop control. Browser and TUI modes are stable.

- **License:** [MIT](https://github.com/zfoong/CraftBot/blob/main/LICENSE). Free to use, host, and monetize (credit required for distribution).
- **Community:** [GitHub](https://github.com/zfoong/CraftBot) · [Discord](https://discord.gg/ZN9YHc37HG)
- **Maintainers:** [CraftOS](https://craftos.net/), [@zfoong](https://github.com/zfoong), [@ahmad-ajmal](https://github.com/ahmad-ajmal)
