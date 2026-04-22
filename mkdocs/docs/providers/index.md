# Providers

CraftBot talks to two kinds of models:

- **LLM providers** — for reasoning, planning, and tool selection
- **VLM providers** — for screen understanding in GUI mode

Both are Bring-Your-Own-Key. Switch providers from the onboarding wizard or `/provider` command.

<div class="grid cards" markdown>

- :material-brain:{ .lg .middle } __[LLM providers](llm.md)__

    ---

    OpenAI, Google Gemini, Anthropic, BytePlus, Ollama.

- :material-eye-outline:{ .lg .middle } __[VLM providers](vlm.md)__

    ---

    Vision models for GUI/desktop automation.

</div>

## Related

- [Environment variables](../configuration/env-vars.md) — API key names for each provider
- [GUI / Vision](../interfaces/gui-vision.md) — how VLMs plug into desktop automation
- [Context engine](../concepts/context-engine.md) — prompt caching strategies per provider
