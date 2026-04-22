# External skills

Skills don't have to live in your repo. The SkillManager can load skills from anywhere on disk, letting you use community-built skills or share your own across projects.

## What you're building

A mechanism to point CraftBot at a directory of skills that lives outside your checkout.

## Step 1 — Point to the path

Edit `app/config/skills_config.json`:

```json
{
  "enabled": true,
  "skill_paths": [
    "~/shared-skills",
    "/opt/craftos/skills",
    "git+https://github.com/alice/skills-pack#my-skills-subdir"
  ]
}
```

Paths resolve in order. Duplicate skill names → first path wins.

## Step 2 — Drop in (or clone) skills

If you have a skill-pack repo:

```bash
mkdir ~/shared-skills
cd ~/shared-skills
git clone https://github.com/alice/skills-pack.git
```

Or install a specific skill:

```bash
mkdir -p ~/shared-skills/awesome-skill
# copy skill.md + any scripts
```

The path structure should match the in-repo format — one folder per skill, `skill.md` at the root.

## Step 3 — Reload

`skills_config.json` is hot-reloaded. Save the file and new skills appear within ~1 second.

```
[SkillManager] Discovered 3 new skills from ~/shared-skills
```

## Step 4 — Verify

```
/skill list
```

Your external skills appear alongside built-ins. Enable / disable with `/skill enable <name>` / `/skill disable <name>`.

## Where to find skills

- **Official** — `skills/` subfolder in the CraftBot repo (dozens of reference skills)
- **Community** — search GitHub for `craftbot skill` or `claude skill`
- **Your own** — version-controlled in your own repo or synced via cloud folder

## Safety considerations

- **Read the skill.md** before enabling — skills can instruct the agent to run shell commands.
- **Review `scripts/`** — bundled shell scripts run with your user privileges.
- **Pin versions** — if you use `git+https://...`, specify a commit or tag, not a branch.

## Per-agent external skills

An [agent bundle](../custom-agent.md) can have its own skill paths in `config.yaml`:

```yaml
# agents/research_agent/config.yaml
skill_paths:
  - agents/research_agent/skills
  - ~/shared-skills/research
```

## Load order

1. Built-in skills (`skills/` in repo root)
2. `skill_paths` from `skills_config.json`, in order
3. Agent-bundle skills from the agent's `config.yaml`

**First match wins** on duplicates.

## Related

- [Write a CraftBot skill](craftbot-skill.md) — the skill format
- [Skills overview](index.md)
- [Skill & action selection](../../concepts/skill-selection.md)
