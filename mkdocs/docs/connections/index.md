# Connections

CraftBot connects to external services in two ways:

- **Invite** *(easy)* — add the CraftOS-hosted bot to your workspace. No keys.
- **Login** *(advanced)* — bring your own bot token, API key, or OAuth credentials.

Run `/cred status` to see every active connection at a glance.

## Start with

<div class="grid cards" markdown>

- :material-key-chain-variant:{ .lg .middle } __[Credentials](credentials.md)__

    ---

    How CraftBot stores tokens, OAuth refresh, and env-var fallbacks.

- :material-server-network:{ .lg .middle } __[MCP servers](mcp.md)__

    ---

    Plug Model Context Protocol tools into CraftBot as native actions.

</div>

## Chat & messaging

<div class="grid cards" markdown>

- [Discord](discord.md)
- [Slack](slack.md)
- [Telegram (Bot)](telegram-bot.md)
- [Telegram (User)](telegram-user.md)
- [WhatsApp Web](whatsapp-web.md)
- [WhatsApp Business](whatsapp-business.md)

</div>

## Productivity & collaboration

<div class="grid cards" markdown>

- [Google Workspace](google-workspace.md)
- [Outlook](outlook.md)
- [Notion](notion.md)
- [LinkedIn](linkedin.md)
- [GitHub](github.md)
- [Jira](jira.md)
- [Twitter](twitter.md)

</div>

## Related

- [Environment variables](../configuration/env-vars.md) — every OAuth variable across integrations
- [Develop :: Custom agent](../develop/custom-agent.md) — bundle integrations into a subclassed agent
