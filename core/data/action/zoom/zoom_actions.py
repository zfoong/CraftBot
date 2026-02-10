from core.action.action_framework.registry import action


@action(
    name="create_zoom_meeting",
    description="Create a new Zoom meeting.",
    action_sets=["zoom"],
    input_schema={
        "topic": {"type": "string", "description": "Meeting topic.", "example": "Weekly Standup"},
        "start_time": {"type": "string", "description": "Start time in ISO 8601 format.", "example": "2024-01-15T10:00:00Z"},
        "duration": {"type": "integer", "description": "Duration in minutes.", "example": 60},
        "timezone": {"type": "string", "description": "Timezone.", "example": "UTC"},
        "agenda": {"type": "string", "description": "Meeting agenda.", "example": "Discuss project updates"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def create_zoom_meeting(input_data: dict) -> dict:
    from core.external_libraries.zoom.external_app_library import ZoomAppLibrary
    ZoomAppLibrary.initialize()
    creds = ZoomAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
    cred = creds[0]
    from core.external_libraries.zoom.helpers.zoom_helpers import create_meeting
    result = create_meeting(cred.access_token, input_data["topic"],
                            start_time=input_data.get("start_time"),
                            duration=input_data.get("duration", 60),
                            timezone=input_data.get("timezone", "UTC"),
                            agenda=input_data.get("agenda", ""))
    return {"status": "success", "result": result}


@action(
    name="list_zoom_meetings",
    description="List scheduled Zoom meetings.",
    action_sets=["zoom"],
    input_schema={
        "meeting_type": {"type": "string", "description": "Type: scheduled, live, upcoming.", "example": "scheduled"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def list_zoom_meetings(input_data: dict) -> dict:
    from core.external_libraries.zoom.external_app_library import ZoomAppLibrary
    ZoomAppLibrary.initialize()
    creds = ZoomAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
    cred = creds[0]
    from core.external_libraries.zoom.helpers.zoom_helpers import list_meetings
    result = list_meetings(cred.access_token,
                           meeting_type=input_data.get("meeting_type", "scheduled"))
    return {"status": "success", "result": result}


@action(
    name="get_zoom_meeting",
    description="Get details of a specific Zoom meeting.",
    action_sets=["zoom"],
    input_schema={
        "meeting_id": {"type": "string", "description": "Zoom meeting ID.", "example": "12345678901"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_zoom_meeting(input_data: dict) -> dict:
    from core.external_libraries.zoom.external_app_library import ZoomAppLibrary
    ZoomAppLibrary.initialize()
    creds = ZoomAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
    cred = creds[0]
    from core.external_libraries.zoom.helpers.zoom_helpers import get_meeting
    result = get_meeting(cred.access_token, input_data["meeting_id"])
    return {"status": "success", "result": result}


@action(
    name="delete_zoom_meeting",
    description="Delete a Zoom meeting.",
    action_sets=["zoom"],
    input_schema={
        "meeting_id": {"type": "string", "description": "Zoom meeting ID to delete.", "example": "12345678901"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def delete_zoom_meeting(input_data: dict) -> dict:
    from core.external_libraries.zoom.external_app_library import ZoomAppLibrary
    ZoomAppLibrary.initialize()
    creds = ZoomAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
    cred = creds[0]
    from core.external_libraries.zoom.helpers.zoom_helpers import delete_meeting
    result = delete_meeting(cred.access_token, input_data["meeting_id"])
    return {"status": "success", "result": result}
