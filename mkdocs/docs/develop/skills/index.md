# Skills

A **skill** is a reusable bundle of actions, prompt instructions, and metadata that the agent can load on demand. Think of it as a plugin that teaches CraftBot a new capability.

<div class="grid cards" markdown>

- :material-file-document-edit-outline:{ .lg .middle } __[Write a CraftBot skill](craftbot-skill.md)__

    ---

    Scaffold → `skill.md` → register → reload → test.

- :material-source-branch:{ .lg .middle } __[External skills](external-skill.md)__

    ---

    Drop third-party skill folders into `skills/` and CraftBot picks them up.

</div>

## Skill vs action vs agent

| Build | When |
|---|---|
| [Action](../custom-action.md) | Single capability, no instructions |
| **Skill** | Bundle of actions + prompt + metadata, loaded on demand |
| [Agent](../custom-agent.md) | Dedicated persona + RAG + custom actions |

## Related

- [Actions](../../concepts/action.md)
- [Skill & action selection](../../concepts/skill-selection.md)
