from agent_core import action

@action(
    name="create_ui_tab",
    description="Create a new dynamic tab in the browser UI. Use this to display structured data (code diffs, stock charts, project plans, or custom content) in a dedicated tab. Preset types: 'code' (file trees, diffs, commits), 'stock' (ticker data, price charts), 'planner' (milestones, kanban tasks), 'custom' (free-form markdown content). The tab will be linked to the current task.",
    default=False,
    action_sets=["browser_ui"],
    parallelizable=False,
    input_schema={
        "tab_type": {
            "type": "string",
            "enum": ["code", "stock", "planner", "custom"],
            "description": "The type of tab to create. 'code' for code analysis/diffs, 'stock' for financial data, 'planner' for project planning, 'custom' for free-form markdown."
        },
        "label": {
            "type": "string",
            "example": "AAPL Analysis",
            "description": "Display label for the tab in the navigation bar."
        },
        "initial_data": {
            "type": "object",
            "description": "Optional initial data to populate the tab. Structure depends on tab_type. For 'custom': {\"content\": \"markdown text\", \"title\": \"...\"}. For 'code': {\"summary\": \"...\", \"files\": [...]}. For 'stock': {\"ticker\": \"AAPL\", \"summary\": \"...\"}. For 'planner': {\"summary\": \"...\", \"tasks\": [...]}.",
            "example": {}
        }
    },
    output_schema={
        "status": {
            "type": "string",
            "example": "ok",
            "description": "'ok' if tab was created, 'error' if creation failed."
        },
        "tab_type": {
            "type": "string",
            "description": "The type of tab that was created."
        },
        "task_id": {
            "type": "string",
            "description": "The task ID the tab is linked to."
        },
        "error": {
            "type": "string",
            "description": "Error message if status is 'error'."
        }
    },
    test_payload={
        "tab_type": "custom",
        "label": "Test Tab",
        "initial_data": {"content": "# Hello\nThis is a test tab."},
        "simulated_mode": True
    }
)
def create_ui_tab(input_data: dict) -> dict:
    import asyncio

    tab_type = input_data.get("tab_type", "custom")
    label = input_data.get("label", "")
    initial_data = input_data.get("initial_data")
    simulated_mode = input_data.get("simulated_mode", False)

    # Validate tab_type
    valid_types = ("code", "stock", "planner", "custom")
    if tab_type not in valid_types:
        return {"status": "error", "error": f"Invalid tab_type '{tab_type}'. Must be one of: {valid_types}"}

    if simulated_mode:
        return {"status": "ok", "tab_type": tab_type, "task_id": "sim-task-001", "label": label}

    # Get the current task ID
    import app.internal_action_interface as iai
    task_id = iai.InternalActionInterface._get_current_task_id()
    if not task_id:
        return {"status": "error", "error": "No active task. Cannot create a tab without an active task context."}

    result = asyncio.run(iai.InternalActionInterface.create_dynamic_tab(
        tab_type=tab_type,
        task_id=task_id,
        label=label,
        initial_data=initial_data,
    ))

    return result
