# VLM providers

Vision-language models (VLMs) let CraftBot **see the screen** in [GUI mode](../interfaces/gui-vision.md). The agent sends a screenshot, asks "where should I click?", and the VLM returns pixel coordinates, a reason, or a structured action.

## Quick start

Pick a VLM provider in [settings.json](../configuration/config-json.md):

```json
{ "model": { "vlm_provider": "anthropic", "vlm_model": null } }
```

Set `null` to use the provider's default. VLM inherits from `llm_provider` if `vlm_provider` is unset.

## Supported providers

Same roster as [LLM providers](llm.md) — VLMs use the same API keys:

| Provider | `vlm_provider` value | Notes |
|---|---|---|
| **Anthropic Claude** | `anthropic` | Sonnet/Opus with vision |
| **OpenAI** | `openai` | GPT-4o family |
| **Google Gemini** | `google` / `gemini` | Gemini 1.5 Pro / 2.x with vision |
| **BytePlus** | `byteplus` | Provider-dependent |
| **Ollama (remote)** | `remote` | Any vision model the server serves (e.g. llava) |

## OmniParser (specialized pipeline)

For dense UI screenshots, a dedicated VLM often under-performs a combination of **detector + VLM**. CraftBot supports [OmniParser](https://github.com/microsoft/OmniParser) as an optional front-end:

```json
{
  "gui": {
    "enabled": true,
    "use_omniparser": true,
    "omniparser_url": "http://127.0.0.1:7861"
  }
}
```

OmniParser runs separately as a Gradio server and returns a structured element list (buttons, labels, icons with bounding boxes). The VLM then operates on that structured data instead of raw pixels — more accurate on complex UIs.

Install via `python install.py --gui`. See [GUI / Vision](../interfaces/gui-vision.md) for full setup.

## Prompt families

GUI mode uses specialized prompts from the [registry](../concepts/prompt.md):

| Prompt | When |
|---|---|
| `GUI_REASONING_PROMPT` | Raw pixel VLM — reason about what's on screen |
| `GUI_REASONING_PROMPT_OMNIPARSER` | OmniParser path — reason over parsed elements |
| `GUI_QUERY_FOCUSED_PROMPT` | Focused query mode — "find the Submit button" |
| `GUI_PIXEL_POSITION_PROMPT` | Pixel coordinate estimation |
| `GUI_ACTION_SPACE_PROMPT` | Lists available GUI actions (click, type, drag, scroll, screenshot) |

Override any of these via `register_prompt(...)` — see [Prompts](../concepts/prompt.md).

## VLM vs LLM costs

VLMs cost more per call than text-only LLMs (images are token-heavy). In GUI mode every step is a VLM call, so runtime can be expensive. Mitigations:

- Enable **OmniParser** — the VLM gets text, not pixels, much cheaper.
- Set a **smaller VLM** (e.g. `gpt-4o-mini` or Haiku) for routine clicks; escalate to larger models only for tricky screens.
- Keep GUI tasks **short** — break long workflows into CLI-mode tasks where possible.

## Related

- [GUI / Vision](../interfaces/gui-vision.md) — the consumer of VLMs
- [LLM providers](llm.md) — same providers, text mode
- [settings.json `gui.*`](../configuration/config-json.md) — the toggle and OmniParser URL
