# Slack

Post messages, list channels and users, search messages, read history, upload files.

## Available actions

- `send_slack_message` — post to a channel or DM
- `list_slack_channels` — list channels in the workspace
- `get_slack_channel_history` — read recent messages
- `list_slack_users` — list workspace members
- `search_slack_messages` — search across channels
- `upload_slack_file` — post a file

## Connect

| Command | What it does |
|---|---|
| `/slack invite` | Install the CraftOS app to your workspace (OAuth flow) |
| `/slack login <bot_token> [workspace_name]` | Connect your own Slack bot token |
| `/slack status` | Show connected workspaces |
| `/slack logout [workspace_id]` | Remove a workspace |

## Prerequisites

=== "Invite (easy)"
    Requires `SLACK_SHARED_CLIENT_ID` and `SLACK_SHARED_CLIENT_SECRET`. Release builds have these embedded. Redirect URI: `https://localhost:8765`.

=== "Login (your own bot)"
    1. Go to [api.slack.com/apps](https://api.slack.com/apps)
    2. Create an app
    3. Add OAuth scopes: `chat:write`, `channels:read`, `users:read`, `channels:history`, `search:read`, `files:write`
    4. Install to workspace
    5. Copy the Bot User OAuth Token (`xoxb-...`)
    6. Run `/slack login <token>`

## Troubleshooting

**OAuth redirect fails** — Slack requires HTTPS. CraftBot uses `https://localhost:8765` — a self-signed cert is served. Click through the browser warning.

**"not_authed" errors** — the bot token is invalid. Re-run `/slack login`.

## Related

- [Credentials](credentials.md)
- [Connections overview](index.md)
