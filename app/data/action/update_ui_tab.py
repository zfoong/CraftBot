from agent_core import action

@action(
    name="update_ui_tab",
    description="Update the data displayed in an existing dynamic browser UI tab. Use this to push new content to a tab that was previously created with create_ui_tab. Data is merged by default (partial updates), or can fully replace existing data. The tab is identified by the current task ID.",
    default=False,
    action_sets=["browser_ui"],
    parallelizable=False,
    input_schema={
        "data": {
            "type": "object",
            "description": (
                "Data payload to send to the tab. Structure depends on the tab type:\n"
                "- code: {\"rawDiff\": \"<raw unified diff output from git diff>\", \"summary\": \"...\", "
                "\"commits\": [{\"hash\": \"...\", \"message\": \"...\", \"author\": \"...\"}]}. "
                "For rawDiff, pass the complete output of `git diff` — the UI will parse and render it with colored +/- lines.\n"
                "- stock: {\"ticker\": \"AAPL\", \"name\": \"Apple Inc.\", \"price\": 150.0, \"change\": 2.5, \"changePercent\": 1.7, "
                "\"summary\": \"...\", \"chartData\": [{\"date\": \"...\", \"open\": 0, \"high\": 0, \"low\": 0, \"close\": 0, \"volume\": 0}]}\n"
                "- planner: {\"title\": \"...\", \"summary\": \"...\", "
                "\"milestones\": [{\"id\": \"...\", \"name\": \"...\", \"date\": \"...\", \"status\": \"pending|completed\"}], "
                "\"tasks\": [{\"id\": \"...\", \"name\": \"...\", \"status\": \"todo|in-progress|done\", \"priority\": \"high|medium|low\", \"assignee\": \"...\", \"dueDate\": \"...\"}]}\n"
                "- custom: {\"content\": \"markdown text\", \"title\": \"...\"}"
            ),
            "example": {"content": "# Updated Content\nNew data here."}
        },
        "replace": {
            "type": "boolean",
            "example": False,
            "description": "If true, replaces all existing tab data with the new data. If false (default), merges the new data into existing data."
        }
    },
    output_schema={
        "status": {
            "type": "string",
            "example": "ok",
            "description": "'ok' if data was sent, 'error' if update failed."
        },
        "task_id": {
            "type": "string",
            "description": "The task ID of the tab that was updated."
        },
        "error": {
            "type": "string",
            "description": "Error message if status is 'error'."
        }
    },
    test_payload={
        "data": {"content": "# Updated\nTest update content."},
        "replace": False,
        "simulated_mode": True
    }
)
def update_ui_tab(input_data: dict) -> dict:
    import asyncio

    tab_data = input_data.get("data", {})
    replace = bool(input_data.get("replace", False))
    simulated_mode = input_data.get("simulated_mode", False)

    if not tab_data:
        return {"status": "error", "error": "No data provided. The 'data' field is required."}

    if simulated_mode:
        return {"status": "ok", "task_id": "sim-task-001", "replace": replace}

    import app.internal_action_interface as iai
    task_id = iai.InternalActionInterface._get_current_task_id()
    if not task_id:
        return {"status": "error", "error": "No active task. Cannot update a tab without an active task context."}

    result = asyncio.run(iai.InternalActionInterface.update_dynamic_tab(
        task_id=task_id,
        tab_data=tab_data,
        replace=replace,
    ))

    return result
