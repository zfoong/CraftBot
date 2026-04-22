# Discord

Send messages to channels, DM users, read messages, list guilds and channels, add reactions.

## Available actions

- `send_discord_message` — post to a channel
- `send_discord_dm` — direct message a user
- `get_discord_messages` — read messages from a channel
- `list_discord_guilds` — list your servers
- `get_discord_channels` — list channels in a guild
- `add_discord_reaction` — react to a message

## Connect

| Command | What it does |
|---|---|
| `/discord invite` | Add the CraftOS bot to your server (opens browser) |
| `/discord invite <guild_id> [name]` | Register a guild after adding the bot |
| `/discord login <bot_token>` | Connect your own Discord bot |
| `/discord login-user <user_token>` | Connect a Discord user account |
| `/discord status` | Show all Discord connections |
| `/discord logout [id]` | Remove a connection |

## Prerequisites

=== "Invite (easy)"
    Requires `DISCORD_SHARED_BOT_ID` env var. Release builds have it embedded.

=== "Login (your own bot)"
    1. Go to [discord.com/developers](https://discord.com/developers/applications)
    2. Create a new application
    3. In Bot tab, create a bot, copy the token
    4. Enable "Message Content Intent" under Privileged Gateway Intents
    5. Run `/discord login <bot_token>`

## Troubleshooting

**Bot sends messages but can't read replies** — enable "Message Content Intent" in the Discord developer portal.

**"Missing Access" errors** — the bot needs to be invited to the server AND have read/write perms in the channel.

## Related

- [Credentials](credentials.md)
- [Connections overview](index.md)
