# settings.json

CraftBot's main runtime configuration is `app/config/settings.json`. It holds the agent name, model provider selection, API keys, feature toggles for memory/proactive/GUI, and endpoint overrides.

!!! note "Two config files"
    There's also a small root-level `config.json` (59 bytes) with install-time flags (`use_conda`, `gui_mode_enabled`). That's for `install.py` and `run.py` — not the runtime config.

## Beginner mental model

- **One file**, JSON.
- **Caches on first read** — `get_settings()` caches the file in memory. Call `invalidate_settings_cache()` or `reload_settings()` to re-read from disk.
- **Last-write-wins** — `save_settings(settings)` overwrites the file.
- Most fields can be edited with the **onboarding wizard** — you rarely need to hand-edit unless scripting.

## Inspect it now

```bash
cat app/config/settings.json
```

Or in Python:

```python
from app.config import get_settings
print(get_settings())
```

## Full schema

```json
{
  "version": "0.0.0",
  "general": {
    "agent_name": "CraftBot",
    "os_language": "en"
  },
  "proactive": { "enabled": true },
  "memory":    { "enabled": true },
  "model": {
    "llm_provider": "anthropic",
    "vlm_provider": "anthropic",
    "llm_model": null,
    "vlm_model": null,
    "slow_mode": false,
    "slow_mode_tpm_limit": 30000
  },
  "api_keys": {
    "openai":    "",
    "anthropic": "",
    "google":    "",
    "byteplus":  ""
  },
  "endpoints": {
    "remote_model_url":     "",
    "byteplus_base_url":    "https://ark.ap-southeast.bytepluses.com/api/v3",
    "google_api_base":      "",
    "google_api_version":   ""
  },
  "web_search": {
    "google_cse_id": ""
  },
  "gui": {
    "enabled":        true,
    "use_omniparser": false,
    "omniparser_url": "http://127.0.0.1:7861"
  }
}
```

## Top-level sections

| Section | Purpose |
|---|---|
| `version` | App version (auto-written on upgrade) |
| `general.agent_name` | Displayed name in the UI and injected into prompts |
| `general.os_language` | Detected on first launch (`en`, `ja`, `zh`, …) — used in prompts |
| `proactive.enabled` | Master switch for [proactive mode](../modes/proactive.md) |
| `memory.enabled` | Master switch for [memory](../concepts/memory.md) |
| `model.*` | Which [LLM & VLM provider](../providers/llm.md) to use, model overrides, slow-mode rate limiting |
| `api_keys.*` | Keys per provider. See [Environment variables](env-vars.md) for env-based alternatives |
| `endpoints.*` | Base URL overrides (Ollama, BytePlus, custom Google API endpoint) |
| `web_search.google_cse_id` | Custom search engine ID for the `web_search` action |
| `gui.*` | GUI mode toggle and OmniParser endpoint |

## Slow mode

`model.slow_mode` adds rate limiting at `model.slow_mode_tpm_limit` tokens per minute. Useful for providers with strict quotas.

```json
{ "model": { "slow_mode": true, "slow_mode_tpm_limit": 30000 } }
```

## Constants (not in JSON)

Some limits live in `app/config.py` as Python constants. Change them by editing the file:

| Constant | Default | Purpose |
|---|---|---|
| `MAX_ACTIONS_PER_TASK` | `500` | Cap to prevent runaway tasks |
| `MAX_TOKEN_PER_TASK` | `12_000_000` | Per-task token budget |
| `PROCESS_MEMORY_AT_STARTUP` | `False` | Whether to run memory processing on launch |
| `MEMORY_PROCESSING_SCHEDULE_HOUR` | `3` | Hour of day (0-23) for daily memory distillation |

## Precedence

For API keys and OAuth credentials, precedence is:

1. **Embedded credentials** (bundled release builds)
2. **OS environment variable** (e.g. `OPENAI_API_KEY`)
3. **`settings.json` → `api_keys`**
4. Empty string (no provider available)

See [Environment variables](env-vars.md) for the env-based approach and [Credentials](../connections/credentials.md) for OAuth handling.

## Hot reload

Changes to `settings.json` are picked up within seconds by the config watcher (`agent_core.config_watcher`). You do not need to restart the agent for most changes — though switching LLM provider mid-task can cause odd behaviour.

!!! tip "Editing safely"
    Use the `/menu` command or onboarding re-run instead of hand-editing. The wizard validates fields and writes atomically.

## Related

- [Environment variables](env-vars.md) — API keys, OAuth secrets via env
- [LLM providers](../providers/llm.md) — provider names and defaults
- [Agent bundle config.yaml](agent-config-yaml.md) — per-agent bundle overrides
- [Onboarding](../start/onboarding.md) — wizard that writes this file
