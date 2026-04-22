# LLM providers

CraftBot talks to large language models through a single `LLMInterface`. Five providers are wired in; switching is one setting change.

## Quick start

Put a key in your environment and pick a provider:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-api03-...
```

```json
// app/config/settings.json
{ "model": { "llm_provider": "anthropic" } }
```

Restart the agent. Done.

## Supported providers

| Provider | `llm_provider` value | Key env var | Default model |
|---|---|---|---|
| **Anthropic Claude** | `anthropic` | `ANTHROPIC_API_KEY` | Latest Sonnet |
| **OpenAI** | `openai` | `OPENAI_API_KEY` | `gpt-4o` family |
| **Google Gemini** | `google` / `gemini` | `GOOGLE_API_KEY` | Latest Gemini |
| **BytePlus (Volc Engine)** | `byteplus` | `BYTEPLUS_API_KEY` | Provider-configured |
| **Ollama (local / remote)** | `remote` | — (uses `REMOTE_MODEL_URL`) | Whatever the server serves |

## Switching providers

Three ways, in order of preference:

1. **Onboarding re-run** — `/menu → Settings → Model` writes to [settings.json](../configuration/config-json.md) atomically.
2. **`/provider <name>`** command — changes the active provider for the session.
3. **Hand-edit [settings.json](../configuration/config-json.md)** — change `model.llm_provider` and restart.

## Model override

By default each provider picks its own recommended model. Override with `model.llm_model`:

```json
{ "model": { "llm_provider": "openai", "llm_model": "gpt-4o-mini" } }
```

## Prompt caching support

Providers differ on prompt caching — the single biggest cost/latency lever:

| Provider | Prefix cache | Session cache (delta) |
|---|---|---|
| Anthropic | Yes (native) | Yes (via delta appends) |
| Google Gemini | Yes (explicit) | Yes |
| BytePlus | Yes (explicit) | Yes |
| OpenAI | Limited (implicit only) | No |
| Ollama | Depends on server | No |

See [Context engine](../concepts/context-engine.md) for how CraftBot exploits this.

## Slow mode

Providers with strict per-minute quotas (e.g. BytePlus) can hit rate limits. Enable slow mode:

```json
{ "model": { "slow_mode": true, "slow_mode_tpm_limit": 30000 } }
```

Requests queue to stay under the TPM limit.

## Ollama / remote servers

Set `REMOTE_MODEL_URL` to point at your Ollama instance:

```bash
# .env
REMOTE_MODEL_URL=http://192.168.1.10:11434
```

```json
{ "model": { "llm_provider": "remote", "llm_model": "llama3.1:70b" } }
```

Any OpenAI-compatible `/v1/chat/completions` endpoint should work.

## Connection test

The agent tests provider connectivity at startup. Per-provider test models live in [`app/config/connection_test_models.json`](../configuration/config-json.md). If the test fails, the agent logs the error and falls back to whatever else is configured.

## Related

- [VLM providers](vlm.md) — vision-language models for GUI mode
- [Environment variables](../configuration/env-vars.md) — the full env-var list
- [settings.json](../configuration/config-json.md) — schema for `model.*`
- [Context engine](../concepts/context-engine.md) — how prompts are built and cached
