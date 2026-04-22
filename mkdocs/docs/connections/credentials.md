# Credentials

All connection tokens, OAuth refresh tokens, API keys, and bot secrets live in a single credential store managed by CraftBot. This page explains *where* credentials live, *how* they're loaded, and the **precedence** across the four possible sources.

## Beginner mental model

- **Embedded credentials** — bundled with release builds. Let users connect Google, Slack, Notion, LinkedIn, and others without creating their own OAuth apps.
- **Environment variables** — override embedded for self-hosted setups. Highest priority after embedded.
- **Connection commands** — `/google login`, `/slack invite`, etc. trigger OAuth or ask for a token. Results are stored in the credential store.
- **Credential store** — JSON files on disk, one per platform. Managed by `agent_core` credential helpers.

## Inspect it now

```
/cred status       # list active connections
/cred integrations # group by platform
```

## Precedence

For OAuth client credentials (the **app**, not the user token):

1. **Embedded** (release builds) — shipped with CraftBot
2. **Environment variable** — `GOOGLE_CLIENT_ID`, `SLACK_SHARED_CLIENT_ID`, etc. See [Environment variables](../configuration/env-vars.md)
3. **`settings.json`** → `api_keys.*`
4. *(nothing)* — connection unavailable

For **user tokens** (your Gmail access token, Slack bot token):

1. Credential store (`app/credentials/` plus OS keychain where available)
2. *(nothing)* — you need to run `/xxx login` again

## Storage

Credentials are stored **locally** in two places:

- **Token files** — `app/credentials/<platform>/<user_id>.json` (OAuth refresh tokens, bot tokens, session strings)
- **OS keychain** (when available) — for secrets the platform deems high-risk (e.g. WhatsApp session cookies)

Nothing is synced to the cloud unless you explicitly configure it.

## The OAuth flow

Most integrations use OAuth 2.0 with PKCE:

1. You type `/google login` (or click a button in the UI).
2. CraftBot generates a PKCE `code_verifier` and `code_challenge`.
3. Your browser opens to the provider's auth page.
4. You approve.
5. Provider redirects to `http://localhost:8765` with an auth code.
6. CraftBot's local HTTP listener grabs the code and exchanges it for tokens.
7. Tokens are saved to the credential store.

Redirect URI is hardcoded to `http://localhost:8765` (HTTPS variant `https://localhost:8765` is used when the provider requires it, e.g. Slack).

## Token types per integration

| Integration | Auth | Client secret needed? |
|---|---|---|
| [Google Workspace](google-workspace.md) | PKCE | No |
| [Outlook](outlook.md) | PKCE | No |
| [Slack](slack.md) | OAuth 2.0 | Yes |
| [Notion](notion.md) | OAuth 2.0 | Yes |
| [LinkedIn](linkedin.md) | OAuth 2.0 | Yes |
| [Discord](discord.md) | Bot token or OAuth invite | No (token) / Yes (invite) |
| [Telegram (Bot)](telegram-bot.md) | Bot token from @BotFather | No |
| [Telegram (User)](telegram-user.md) | MTProto API (api_id + api_hash) | — |
| [WhatsApp Web](whatsapp-web.md) | QR scan via Playwright | — |
| [WhatsApp Business](whatsapp-business.md) | Meta API token | — |
| [GitHub](github.md) | Personal access token | — |
| [Jira](jira.md) | API token + workspace URL | — |
| [Twitter](twitter.md) | API key + secret (v2) | — |

## Managing credentials

| Command | Effect |
|---|---|
| `/<platform> login [args]` | Start auth flow or set a token |
| `/<platform> logout [id]` | Remove a stored credential |
| `/<platform> status` | Check whether the integration is connected |
| `/<platform> invite` | Use CraftOS-hosted app (where supported) |
| `/cred status` | List every integration + state |
| `/cred <platform> connect` | Alias for `/xxx login` from the universal credentials panel |

## Rotating credentials

- **OAuth tokens** refresh automatically via the stored refresh token. Rotate by running `/xxx logout` then `/xxx login`.
- **Bot tokens** (Discord, Telegram Bot): revoke the old token in the provider's dashboard, generate a new one, run `/xxx login <new_token>`.
- **API keys** (GitHub, Jira, Twitter, Recall.ai): re-run `login` with the new key.

## Security considerations

- `app/credentials/` is **gitignored** — never commit it.
- Tokens are **masked in logs** — if a secret leaks into a log, that's a bug; please report.
- Use env vars (or the keychain path) instead of `api_keys` in `settings.json` for better security posture.

## Related

- [Environment variables](../configuration/env-vars.md) — the env-based source
- [`settings.json`](../configuration/config-json.md) — the `api_keys` source
- [Connections overview](index.md)
