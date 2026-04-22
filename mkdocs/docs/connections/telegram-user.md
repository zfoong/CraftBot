# Telegram (User)

Connect CraftBot **as you** — your personal Telegram account, via Telegram's MTProto API. Lets CraftBot send messages on your behalf, read DMs, and access private groups.

For public-bot use cases, see [Telegram (Bot)](telegram-bot.md) instead.

## Available actions

- `send_telegram_user_message` — send as yourself
- `send_telegram_user_file` — send a file
- `get_telegram_chats` — list your recent chats
- `read_telegram_messages` — read messages from a chat
- `search_telegram_user_contacts` — search your contacts

## Connect

Two-step phone auth:

```
/telegram login-user <phone_number>
# Telegram sends a code to your phone
/telegram login-user <phone_number> <code> [2fa_password]
```

| Command | What it does |
|---|---|
| `/telegram login-user <phone>` | Step 1: request verification code |
| `/telegram login-user <phone> <code> [2fa]` | Step 2: verify and authenticate |
| `/telegram status` | Show user-account connections |
| `/telegram logout [phone]` | Remove connection |

## Prerequisites

- Telegram API credentials (**not** a bot token):
  1. Go to [my.telegram.org](https://my.telegram.org)
  2. → API development tools → Create new application
  3. Save `api_id` and `api_hash`
- Set `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` in `.env`
- `telethon` package: `pip install telethon`

Session files (`*.session`) are stored in the credential store — back these up to avoid re-verifying on every machine.

## Troubleshooting

**"Telethon not installed"** — run `pip install telethon` in the CraftBot env.

**"Wrong 2FA password"** — 2FA is separate from the SMS code. Check if you have 2FA enabled in Telegram and include the password as the third argument.

**Session lost after restart** — make sure the session file persists. Some containers nuke `/tmp/*` on restart — mount the credential dir.

## Security note

A user-account connection lets CraftBot send messages as you to any contact. Review actions carefully before enabling tier-2+ automations that send Telegram messages.

## Related

- [Telegram (Bot)](telegram-bot.md) — bot alternative (safer, more limited)
- [Credentials](credentials.md)
- [Connections overview](index.md)
