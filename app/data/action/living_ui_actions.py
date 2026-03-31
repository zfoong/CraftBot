"""Living UI actions for agent to notify UI status and progress."""

from agent_core import action


@action(
    name="living_ui_notify_ready",
    description=(
        "Notify the browser that a Living UI project is ready and running. "
        "Call this after successfully building and launching the Living UI. "
        "The browser will then display the Living UI to the user."
    ),
    default=False,
    mode="CLI",
    action_sets=["living_ui"],
    parallelizable=False,
    input_schema={
        "project_id": {
            "type": "string",
            "example": "abc12345",
            "description": "The Living UI project ID (provided in task instruction).",
        },
        "url": {
            "type": "string",
            "example": "http://localhost:3100",
            "description": "The URL where the Living UI is accessible.",
        },
        "port": {
            "type": "integer",
            "example": 3100,
            "description": "The port number the Living UI is running on.",
        },
    },
    output_schema={
        "status": {
            "type": "string",
            "example": "success",
            "description": "Result of the notification.",
        },
        "message": {
            "type": "string",
            "example": "Living UI is now ready",
            "description": "Status message.",
        },
    },
    test_payload={
        "project_id": "test123",
        "url": "http://localhost:3100",
        "port": 3100,
        "simulated_mode": True,
    },
)
def living_ui_notify_ready(input_data: dict) -> dict:
    """Notify browser that a Living UI is ready to display."""
    import asyncio

    project_id = input_data.get("project_id", "")
    url = input_data.get("url", "")
    port = input_data.get("port", 0)
    simulated_mode = input_data.get("simulated_mode", False)

    if not project_id:
        return {
            "status": "error",
            "message": "project_id is required",
        }

    if not url or not port:
        return {
            "status": "error",
            "message": "url and port are required",
        }

    if simulated_mode:
        return {
            "status": "success",
            "message": f"Living UI {project_id} is now ready at {url}",
        }

    try:
        # Use the callback system to broadcast the notification
        from app.living_ui import broadcast_living_ui_ready

        # Run the async broadcast function
        success = asyncio.run(broadcast_living_ui_ready(project_id, url, port))

        if success:
            return {
                "status": "success",
                "message": f"Living UI {project_id} is now ready at {url}",
            }
        else:
            return {
                "status": "error",
                "message": "Broadcast callback not registered. Browser adapter may not be initialized.",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to notify: {str(e)}",
        }


@action(
    name="living_ui_restart",
    description=(
        "Restart a running Living UI project (backend + frontend). "
        "Use this after modifying backend or frontend code so changes take effect. "
        "Stops the entire project and relaunches it on the same ports."
    ),
    default=False,
    mode="CLI",
    action_sets=["living_ui"],
    parallelizable=False,
    input_schema={
        "project_id": {
            "type": "string",
            "example": "5a58a160",
            "description": "The Living UI project ID (from living_ui_projects.json).",
        },
    },
    output_schema={
        "status": {
            "type": "string",
            "example": "success",
            "description": "Result of the restart operation.",
        },
        "message": {
            "type": "string",
            "example": "Living UI '5a58a160' restarted",
            "description": "Status message.",
        },
        "url": {
            "type": "string",
            "example": "http://localhost:3100",
            "description": "The frontend URL after restart.",
        },
        "backend_url": {
            "type": "string",
            "example": "http://localhost:3101",
            "description": "The backend URL after restart.",
        },
    },
    test_payload={
        "project_id": "test123",
        "simulated_mode": True,
    },
)
def living_ui_restart(input_data: dict) -> dict:
    """Restart a running Living UI project."""
    import asyncio

    project_id = input_data.get("project_id", "")
    simulated_mode = input_data.get("simulated_mode", False)

    if not project_id:
        return {
            "status": "error",
            "message": "project_id is required",
        }

    if simulated_mode:
        return {
            "status": "success",
            "message": f"Living UI '{project_id}' restarted",
            "url": "http://localhost:3100",
            "backend_url": "http://localhost:3101",
        }

    try:
        from app.living_ui import restart_living_ui

        result = asyncio.run(restart_living_ui(project_id))
        return result
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to restart: {str(e)}",
        }


@action(
    name="living_ui_report_progress",
    description=(
        "Report progress during Living UI creation. "
        "Use this to keep the user informed about the development status. "
        "The browser will display the progress to the user."
    ),
    default=False,
    mode="CLI",
    action_sets=["living_ui"],
    parallelizable=True,
    input_schema={
        "project_id": {
            "type": "string",
            "example": "abc12345",
            "description": "The Living UI project ID.",
        },
        "phase": {
            "type": "string",
            "enum": ["initializing", "scaffolding", "coding", "testing", "building", "launching"],
            "example": "coding",
            "description": "Current development phase.",
        },
        "progress": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "example": 50,
            "description": "Progress percentage (0-100).",
        },
        "message": {
            "type": "string",
            "example": "Implementing view components...",
            "description": "Human-readable status message.",
        },
    },
    output_schema={
        "status": {
            "type": "string",
            "example": "success",
            "description": "Result of the progress report.",
        },
    },
    test_payload={
        "project_id": "test123",
        "phase": "coding",
        "progress": 50,
        "message": "Test progress message",
        "simulated_mode": True,
    },
)
def living_ui_report_progress(input_data: dict) -> dict:
    """Report Living UI creation progress to browser."""
    import asyncio

    project_id = input_data.get("project_id", "")
    phase = input_data.get("phase", "")
    progress = input_data.get("progress", 0)
    message = input_data.get("message", "")
    simulated_mode = input_data.get("simulated_mode", False)

    if not project_id:
        return {
            "status": "error",
            "message": "project_id is required",
        }

    if simulated_mode:
        return {"status": "success"}

    try:
        # Use the callback system to broadcast progress
        from app.living_ui import broadcast_living_ui_progress

        # Run the async broadcast function
        success = asyncio.run(broadcast_living_ui_progress(
            project_id, phase, progress, message
        ))

        if success:
            return {"status": "success"}
        else:
            return {
                "status": "error",
                "message": "Broadcast callback not registered. Browser adapter may not be initialized.",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to report progress: {str(e)}",
        }
