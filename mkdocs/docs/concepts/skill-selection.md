# Skill & action selection

Action selection is the decision the LLM makes every iteration: *given what the user asked and what's happened so far, which [action](action.md) (or actions) do I run next?* Getting this right is the difference between an agent that helps and one that spins.

## Beginner mental model

- The **action router** is a class with four selection methods — one per workflow.
- Each method builds a prompt from (a) a template, (b) the current [event stream](event-stream.md), (c) the relevant [memory](memory.md) for the query, and (d) a filtered list of action candidates.
- The LLM returns a **list** of action decisions in JSON: `[{"action_name": "X", "parameters": {...}, "reasoning": "..."}, ...]`. Multiple actions can run **in parallel** within one iteration.
- If the LLM returns bad JSON, the router retries up to **3 times** with augmented error feedback before giving up.

## Inspect it now

The router logs every selection:

```bash
tail -f logs/*.log | grep -E "PARALLEL|ACTION|FORMAT ERROR"
```

## Example output

```text
[PARALLEL] Conversation mode selected 1 action(s): ['task_start']
[PARALLEL] Complex task mode selected 2 action(s): ['web_search', 'task_update_todos']
```

## Four selection methods

The router has one method per [workflow](agent-loop.md#routing-rules), each with its own prompt and candidate filtering:

| Method | Workflow | Candidates | Prompt |
|---|---|---|---|
| `select_action` | Conversation | `send_message`, `task_start`, `ignore`, integration mgmt actions, + messaging actions for connected platforms | `SELECT_ACTION_PROMPT` |
| `select_action_in_simple_task` | Simple task | Actions from the task's `action_sets` | `SELECT_ACTION_IN_SIMPLE_TASK_PROMPT` |
| `select_action_in_task` | Complex task | Actions from the task's `action_sets` | `SELECT_ACTION_IN_TASK_PROMPT` |
| `select_action_in_GUI` | GUI task | GUI-visible actions + `GUI_ACTION_SPACE_PROMPT` | `SELECT_ACTION_IN_GUI_PROMPT` |

Each prompt is in the [prompt registry](prompt.md) — override it to change behaviour.

## Candidate filtering

Actions are filtered by **visibility mode** before being shown to the LLM:

| Action `visibility_mode` | Shown when |
|---|---|
| `"CLI"` | Non-GUI workflows only |
| `"GUI"` | GUI workflow only |
| `"ALL"` / `None` | Both |

This prevents the LLM from selecting e.g. `mouse_click` during a conversation task.

## Dynamic messaging actions

In conversation mode, connected [external integrations](../connections/index.md) automatically contribute send/read actions to the candidate list. Example: after `/slack login`, `send_slack_message` appears alongside `send_message`. Disconnect the integration (`/slack logout`) and the action disappears.

## Parallel action execution

The router can return multiple actions per iteration. These run **in parallel** via `_execute_actions` (see [Agent loop](agent-loop.md#the-action-beat)). Useful for e.g. "update my todos AND read the next doc" — one turn, two actions.

## Format-error retry

The LLM sometimes returns malformed JSON. The router retries up to **3 times** with an augmented prompt that includes the previous attempt and the parse error. If all three fail, it raises `ValueError` and the task aborts to prevent token burn.

```text
[FORMAT ERROR] Conversation mode attempt 2/3: Expected JSON array, got string
```

## Skills inject instructions, not actions

**Skills** (see [Write a CraftBot skill](../develop/skills/craftbot-skill.md)) are orthogonal to action selection. A skill is a *prompt-fragment + metadata* bundle that gets injected into the system prompt when its parent task has `selected_skills: ["my-skill"]`. Skills don't add actions to the candidate list — they add *guidance* about how to use existing actions.

Example: the `heartbeat-processor` skill tells the agent *"read PROACTIVE.md first, then filter by time/day, then execute"* — it doesn't provide any new actions, it provides a *strategy* over existing ones.

## Adding your own decision logic

Three paths to influence selection:

1. **Override the prompt** — change `SELECT_ACTION_IN_TASK_PROMPT` via [`register_prompt()`](prompt.md).
2. **Add a skill** — inject strategy into tasks that opt in via `selected_skills`.
3. **Subclass the agent** — override `_select_action()` in [your agent bundle](../develop/custom-agent.md) for total control.

## Related

- [Agent loop](agent-loop.md) — where selection fits in the cycle
- [Actions](action.md) — the vocabulary the router chooses from
- [Prompts](prompt.md) — the four selection prompts and the registry
- [Skills](../develop/skills/index.md) — strategy injection into prompts
