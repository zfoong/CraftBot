# Configuration

Three surfaces control every CraftBot knob:

<div class="grid cards" markdown>

- :material-cog-outline:{ .lg .middle } __[config.json](config-json.md)__

    ---

    Runtime flags: GUI mode, conda usage, memory, proactive, model selection.

- :material-file-cog-outline:{ .lg .middle } __[Agent bundle config.yaml](agent-config-yaml.md)__

    ---

    Per-agent bundle: role, data_dir, rag_dir, LLM provider.

- :material-key-variant:{ .lg .middle } __[Environment variables](env-vars.md)__

    ---

    API keys, OAuth secrets, paths. Via `.env` or OS env.

</div>

## Precedence (highest to lowest)

1. **`.env` file in the project root** — loaded first at startup
2. **OS environment variables** — overlay on top of `.env`
3. **`config.json`** — runtime flags not covered by env
4. **Onboarding wizard answers** — written into `config.json` and credential store on first run

## Related

- [Onboarding](../start/onboarding.md) — first-run wizard that writes much of this for you
- [Credentials](../connections/credentials.md) — where tokens and OAuth refresh live
