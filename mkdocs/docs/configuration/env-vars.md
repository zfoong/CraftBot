# Environment variables

CraftBot reads environment variables for LLM API keys, optional endpoint URLs, and OAuth client credentials. Env vars are the **highest-precedence** override after embedded credentials — they win over [`settings.json`](config-json.md) entries of the same name.

## Beginner mental model

- Drop an **`.env` file** at the project root (copy from `.env.example`) — CraftBot loads it at startup.
- Or set them as **real OS environment variables** — equivalent effect.
- Anything **set to an empty string is treated as unset** and falls back to `settings.json` or embedded credentials.

## Inspect it now

```bash
cat .env.example
```

Or view what the app will actually use:

```python
from app.config import get_api_key
print(get_api_key("anthropic"))
```

## LLM provider keys

Set at least one:

| Env var | Provider |
|---|---|
| `OPENAI_API_KEY` | OpenAI — see [LLM providers](../providers/llm.md) |
| `GOOGLE_API_KEY` | Google Gemini — see [LLM providers](../providers/llm.md) |
| `ANTHROPIC_API_KEY` | Anthropic Claude — see [LLM providers](../providers/llm.md) |
| `BYTEPLUS_API_KEY` | BytePlus (Volc Engine) — see [LLM providers](../providers/llm.md) |
| `REMOTE_MODEL_URL` | Ollama server URL (e.g. `http://192.168.1.10:11434`) |

## GUI / Vision

| Env var | Purpose |
|---|---|
| `OMNIPARSER_BASE_URL` | Gradio URL for [OmniParser](../interfaces/gui-vision.md). Leave unset for `http://localhost:7861` |

## OAuth client credentials

Embedded credentials ship with release builds. Set these only if you're running your own OAuth apps or the embedded client expired.

| Env var | Used by |
|---|---|
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | [Google Workspace](../connections/google-workspace.md) (PKCE — only client_id required) |
| `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` | [LinkedIn](../connections/linkedin.md) |
| `OUTLOOK_CLIENT_ID` | [Outlook](../connections/outlook.md) (PKCE — only client_id) |
| `SLACK_SHARED_CLIENT_ID` / `SLACK_SHARED_CLIENT_SECRET` | [Slack](../connections/slack.md) |
| `NOTION_SHARED_CLIENT_ID` / `NOTION_SHARED_CLIENT_SECRET` | [Notion](../connections/notion.md) |
| `TELEGRAM_SHARED_BOT_TOKEN` / `TELEGRAM_SHARED_BOT_USERNAME` | [Telegram (Bot)](../connections/telegram-bot.md) |
| `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` | [Telegram (User)](../connections/telegram-user.md) |

## `.env` file layout

CraftBot reads the root-level `.env` (copy from `.env.example`):

```bash
# Copy the template
cp .env.example .env
# Edit it
$EDITOR .env
```

Each line is `KEY=value`. Blank lines and `#` comments are allowed. Quote values that contain spaces or special chars:

```bash
ANTHROPIC_API_KEY="sk-ant-api03-..."
GOOGLE_CLIENT_ID="123456789.apps.googleusercontent.com"
```

## Precedence

For any piece of configuration that has multiple sources, CraftBot checks in order:

1. **Embedded credentials** (only for OAuth clients, bundled with release builds)
2. **OS environment variable** (including `.env` file)
3. **`settings.json` → `api_keys` / `endpoints`**
4. Empty / unset → feature disabled

## Where env vars are read

- LLM keys via `app/config.py` — checks env first, then settings.
- OAuth creds via `app/config.py` — checks embedded, then env, then returns empty.
- Ollama URL via `app/config.py` — falls back to `http://localhost:11434`.

## `.env` vs settings.json — which to use?

| Use env vars for | Use settings.json for |
|---|---|
| Secrets (API keys, tokens) | User-facing preferences |
| Things you don't want committed to git | Model/provider selection |
| CI / deployment | Integration-specific options |
| Per-user local overrides | Things the onboarding wizard writes |

Both are git-ignored by default.

## Related

- [`settings.json`](config-json.md) — the JSON-based counterpart
- [Credentials](../connections/credentials.md) — OAuth flow specifics
- [LLM providers](../providers/llm.md) — per-provider key requirements
