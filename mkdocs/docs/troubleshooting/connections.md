# Connection issues

OAuth, token, and integration failures.

## OAuth redirect fails

**Symptom:** Browser opens, you approve, but CraftBot says "OAuth timed out."

**Causes:**

- **Firewall / security software** blocks the local listener on port 8765. Temporarily disable, retry, re-enable.
- **HTTPS mismatch** — Slack requires `https://localhost:8765`. The self-signed cert causes a browser warning — click through (Advanced → Proceed).
- **Port in use** — another process is on 8765. Stop it or restart CraftBot.

## OAuth succeeded but action fails

**Symptom:** `/google status` says connected, but `send_gmail` errors with "unauthorized."

**Causes:**

- **Scope mismatch** — you approved a limited scope. Re-run `/google logout` + `/google login` and approve everything.
- **Token revoked** — Google revoked the token (user account changed, password reset, suspicious activity). Re-login.
- **Wrong Client ID** — if you set a custom `GOOGLE_CLIENT_ID` but are using embedded tokens, remove the env var or re-login.

## Token refresh fails

**Symptom:** Integration worked yesterday; today all calls error with "invalid_grant."

**Fix:** The refresh token was revoked. Run `/xxx logout` then `/xxx login`.

Per-provider refresh lifetimes:

| Provider | Refresh token lifetime |
|---|---|
| Google | 6 months of inactivity / 200 refresh tokens per client per user |
| Outlook | 90 days |
| Slack | Rotating — refresh on every use |
| Notion | Long-lived until revoked |
| LinkedIn | 60 days |

## Bot token invalid (Discord / Telegram bot)

**Symptom:** `/discord login <token>` succeeds but messages fail.

**Fix:**

- Regenerate the token in the provider's developer portal.
- `/discord logout` + `/discord login <new_token>`.
- For Discord: ensure the bot was **invited to the server** with correct permissions.
- For Telegram: `/start` your bot in Telegram to initialize chat.

## WhatsApp QR code doesn't appear

**Symptom:** `/whatsapp login` hangs.

**Causes:**

- **Playwright not installed** — `pip install playwright && playwright install chromium`.
- **Chromium headless fails** — Linux may need `playwright install-deps` for system libraries.
- **Browser profile corrupted** — delete the WhatsApp session folder in the credential store, retry.

## Telegram User auth: "Wrong code"

**Symptom:** Step 2 of `login-user` rejects the SMS code.

**Causes:**

- **Code expired** — Telegram codes are short-lived. Request a new one.
- **2FA enabled** — include the password as the third argument: `/telegram login-user <phone> <code> <2fa_pwd>`.
- **Wrong phone format** — include country code with `+`: `+81...` not `0...`.

## MCP server won't connect

**Symptom:** MCP server in `mcp_config.json` shows "disconnected."

**Debug steps:**

1. Check the server runs manually: `npx -y @modelcontextprotocol/server-filesystem /path`
2. Check `enabled: true` in the config
3. Tail logs for `[MCP]` errors
4. Verify `env: {...}` has all required vars set
5. For SSE/WebSocket: test the URL with `curl` or `websocat`

See [MCP servers](../connections/mcp.md).

## Webhook not receiving messages (WhatsApp Business)

**Symptom:** Outbound works; inbound is silent.

**Fix:** Webhooks require Meta to reach your CraftBot. Options:

- **Tunnel** — expose your localhost via ngrok / Cloudflare Tunnel, configure the public URL in Meta.
- **Serverless forwarder** — have Meta hit a Lambda/Worker that forwards to CraftBot over your tunnel.
- **Skip webhooks** — use polling via `get_whatsapp_business_messages` on a schedule.

## `/cred status` says "embedded" but login fails

You're on a release build with embedded credentials, but the embedded Client ID expired or was revoked. Options:

- Wait for the next release, or
- Create your own OAuth app and set `GOOGLE_CLIENT_ID` (etc.) in `.env`. See [Credentials](../connections/credentials.md).

## Related

- [Credentials](../connections/credentials.md) — precedence rules
- [Connections overview](../connections/index.md) — per-platform pages
- [Logs](../concepts/logs.md) — where auth errors appear
