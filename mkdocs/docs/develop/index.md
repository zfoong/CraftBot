# Develop

Extend CraftBot. Five paths, all with a scaffold → write → register → reload → test flow.

<div class="grid cards" markdown>

- :material-toolbox-outline:{ .lg .middle } __[Skills overview](skills/index.md)__

    ---

    What skills are, when to create one, where they live.

- :material-file-document-edit-outline:{ .lg .middle } __[Write a CraftBot skill](skills/craftbot-skill.md)__

    ---

    Step-by-step: scaffold a skill, define tools, reload, test.

- :material-source-branch:{ .lg .middle } __[External skills](skills/external-skill.md)__

    ---

    Load third-party skills from the `skills/` directory.

- :material-lightning-bolt-outline:{ .lg .middle } __[Custom action](custom-action.md)__

    ---

    Write a single action with input/output schemas.

- :material-package-variant:{ .lg .middle } __[Custom agent](custom-agent.md)__

    ---

    Subclass the base agent into a bundle (`config.yaml` + role + RAG + custom actions).

</div>

## What to build

| Goal | Build |
|---|---|
| One-off capability (e.g. "query our internal API") | [Custom action](custom-action.md) |
| Reusable set of actions + prompt + metadata | [CraftBot skill](skills/craftbot-skill.md) |
| Dedicated agent with its own personality/knowledge | [Custom agent](custom-agent.md) |
| Import tools from an existing MCP server | [MCP servers](../connections/mcp.md) |

## Related

- [Actions](../concepts/action.md) — the primitive every extension extends
- [Skill & action selection](../concepts/skill-selection.md) — how the agent picks between what you built
- [Actions catalogue](../reference/actions.md) — every built-in action as a baseline
