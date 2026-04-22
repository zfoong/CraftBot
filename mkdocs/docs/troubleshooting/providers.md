# Provider issues

LLM / VLM provider problems — rate limits, model errors, context window overruns.

## Rate limited

**Symptom:** `LLMConsecutiveFailureError` or `429 Too Many Requests` in logs.

**Fixes:**

- **Enable slow mode** — adds rate limiting client-side:

    ```json
    { "model": { "slow_mode": true, "slow_mode_tpm_limit": 30000 } }
    ```

- **Lower TPM limit** if you hit mid-minute limits.
- **Switch providers** — some providers (Anthropic, Gemini) have generous free tiers; BytePlus has strict per-minute limits on trial tiers.

## Consecutive failures

**Symptom:** Logs say `[LLM] consecutive failures: 5`. Event-stream summarization falls back to prune-without-summary.

**Why:** The LLM returned an error (rate limit, outage, invalid key) 5 times in a row. CraftBot backs off.

**Fix:**

- Check the provider's status page
- Verify the API key is valid (`/menu` → Models → test)
- Wait a few minutes for the circuit breaker to reset, or restart the agent

## Context window overrun

**Symptom:** `context_length_exceeded` error from the LLM.

**Fixes:**

- Event stream should auto-summarize at 30k tokens. If it hasn't kicked in, check `[EventStream] Triggering summarization` in logs.
- Large task with many todos? Break it into sub-tasks.
- Using a small-context model (e.g. GPT-3.5) — switch to a bigger one.

## Model not found

**Symptom:** `model_not_found` on startup.

**Fix:** `model.llm_model` in [settings.json](../configuration/config-json.md) is misspelled or not available to your account. Leave it `null` to use the provider's default, or set a known model:

| Provider | Safe default |
|---|---|
| Anthropic | `claude-sonnet-4-6` |
| OpenAI | `gpt-4o` |
| Google | `gemini-2.0-flash` |
| BytePlus | (provider-configured) |
| Ollama | Whatever is `ollama list`'d on the server |

## API key invalid

**Symptom:** `authentication_error` / `invalid_api_key` immediately on startup.

**Fix:** Re-check the key. Common mistakes:

- **Extra whitespace** — trim leading/trailing spaces
- **Wrong env var** — `OPENAI_API_KEY` vs `ANTHROPIC_API_KEY`
- **Wrong provider selected** — key is for Anthropic but `llm_provider: "openai"`
- **Scope missing** (Google) — check your GCP project has the right APIs enabled

## Prompt caching not helping

**Symptom:** Each LLM call bills the full prompt; no cost reduction over long tasks.

**Check:**

- **Provider supports caching?** OpenAI has only *implicit* caching. Switch to Anthropic / Gemini / BytePlus for explicit caching.
- **System prompt churn** — is `AGENT.md` or `USER.md` being edited mid-task? That invalidates the prefix cache.
- **Session cache reset** — event-stream summarization invalidates session caches. Happens every ~30k tokens; expected.

See [Context engine concept](../concepts/context-engine.md).

## VLM calls fail in GUI mode

**Symptom:** `content_policy_violation` or `image_processing_error` on every GUI iteration.

**Fixes:**

- **Wrong VLM model** — set `vlm_model` to a known vision-capable model (e.g. `gpt-4o`, `gemini-2.0-flash`).
- **Image too large** — some providers cap at ~5 MB. Lower your screen resolution or enable OmniParser.
- **Policy block** — some providers block images of certain UIs (e.g. screens showing phone numbers). Check the error message.

## Ollama server unreachable

**Symptom:** `Connection refused` to `REMOTE_MODEL_URL`.

**Fixes:**

- **Server not running** — `ollama serve` on the host machine.
- **Wrong URL** — default Ollama port is 11434. Use the full URL: `http://192.168.1.10:11434`.
- **Firewall** — Ollama by default binds to `127.0.0.1` only. Set `OLLAMA_HOST=0.0.0.0:11434` on the server to allow remote access.
- **Model not pulled** — `ollama pull <model>` first.

## BytePlus regional issues

**Symptom:** BytePlus works intermittently or returns timeout.

**Check:** `endpoints.byteplus_base_url`. Default is `https://ark.ap-southeast.bytepluses.com/api/v3` (Singapore). Pick the closest region to your machine.

## Related

- [LLM providers](../providers/llm.md)
- [VLM providers](../providers/vlm.md)
- [Context engine](../concepts/context-engine.md) — where caching lives
- [Logs](../concepts/logs.md)
