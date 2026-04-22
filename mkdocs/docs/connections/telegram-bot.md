# Telegram (Bot)

Connect a Telegram **bot** (created via @BotFather). Best for public channels, groups, and notifications.

For personal messaging via your own Telegram account, see [Telegram (User)](telegram-user.md) instead.

## Available actions

- `send_telegram_bot_message` — send text
- `send_telegram_photo` — send image
- `get_telegram_updates` — poll new messages
- `get_telegram_chat` — look up chat by id/username
- `search_telegram_contact` — search contacts by name

## Connect

| Command | What it does |
|---|---|
| `/telegram invite` | Connect the shared CraftOS Telegram bot |
| `/telegram login <bot_token>` | Connect your own bot from @BotFather |
| `/telegram status` | Show all Telegram connections |
| `/telegram logout [id]` | Remove a connection |

## Prerequisites

=== "Invite (easy)"
    Requires `TELEGRAM_SHARED_BOT_TOKEN` and `TELEGRAM_SHARED_BOT_USERNAME`. Set these in `.env` or use embedded credentials.

=== "Login (your own bot)"
    1. Message [@BotFather](https://t.me/BotFather) on Telegram
    2. `/newbot` → follow prompts → save the token
    3. Run `/telegram login <token>`
    4. In Telegram, `/start` your bot to initialize chat

## Troubleshooting

**Bot doesn't see messages in groups** — by default, bots only see messages addressed to them. In @BotFather, disable Privacy Mode to see all group messages.

**`get_telegram_updates` returns nothing** — Telegram's bot API uses long-polling. The first call after a gap returns immediately; subsequent calls hold open for up to ~30s waiting for new events.

## Related

- [Telegram (User)](telegram-user.md) — use your own account via MTProto
- [Credentials](credentials.md)
- [Connections overview](index.md)
