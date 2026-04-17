# core/data/action/skill_management.py
"""
Skill Management Actions

These actions allow the agent to dynamically list and switch skills during task execution.
Both actions belong to the 'core' set and are always available.
"""

from agent_core import action


@action(
    name="list_skills",
    description=(
        "List all enabled skills with their names and descriptions. "
        "Use this to discover available skills before using 'use_skill'."
    ),
    default=False,
    mode="ALL",
    action_sets=["core"],
    input_schema={},
    output_schema={
        "skills": {
            "type": "object",
            "description": "Dictionary of enabled skill names to their descriptions.",
        },
    },
    test_payload={
        "simulated_mode": True,
    },
)
def list_skills(input_data: dict) -> dict:
    """List all enabled skills with their names and descriptions."""
    simulated_mode = input_data.get("simulated_mode", False)

    if simulated_mode:
        return {
            "skills": {
                "pdf": "Read and create PDF documents",
                "docx": "Read and create Word documents",
            },
        }

    import app.internal_action_interface as iai

    try:
        result = iai.InternalActionInterface.list_skills()
        return result
    except Exception as e:
        return {"error": str(e)}


@action(
    name="use_skill",
    description=(
        "Activate a skill for the current task, replacing the current skill in the system prompt. "
        "ONLY use this action when the current skill need to be completely replaced with a new skill. "
        "If you only need to read a skill's instructions while keeping the current skill in context, "
        "find the skill directory and use 'read_file' on the skill's SKILL.md file instead. "
        "Use 'list_skills' first to see enabled skill first."
    ),
    default=False,
    mode="ALL",
    action_sets=["core"],
    parallelizable=False,
    input_schema={
        "skill_name": {
            "type": "string",
            "description": "Name of the skill to activate.",
            "example": "pdf",
        },
    },
    output_schema={
        "success": {
            "type": "boolean",
            "description": "Whether the skill was activated successfully.",
        },
        "active_skill": {
            "type": "string",
            "description": "Name of the now-active skill.",
        },
        "skill_description": {
            "type": "string",
            "description": "Description of the activated skill.",
        },
        "previous_skills": {
            "type": "array",
            "description": "List of previously active skill names that were replaced.",
        },
        "added_action_sets": {
            "type": "array",
            "description": "Action sets that were added as recommended by the skill.",
        },
    },
    test_payload={
        "skill_name": "pdf",
        "simulated_mode": True,
    },
)
def use_skill(input_data: dict) -> dict:
    """Activate a skill, replacing the current skill in the system prompt."""
    skill_name = input_data.get("skill_name", "")
    simulated_mode = input_data.get("simulated_mode", False)

    if not skill_name:
        return {
            "success": False,
            "error": "No skill_name specified.",
        }

    if simulated_mode:
        return {
            "success": True,
            "active_skill": skill_name,
            "skill_description": "Simulated skill description",
            "previous_skills": [],
            "added_action_sets": [],
        }

    import app.internal_action_interface as iai

    try:
        result = iai.InternalActionInterface.use_skill(skill_name)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
