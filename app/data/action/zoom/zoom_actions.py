from agent_core import action


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
    try:
        from app.external_comms.platforms.zoom import ZoomClient
        client = ZoomClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
        result = client.create_meeting(
            input_data["topic"],
            start_time=input_data.get("start_time"),
            duration=input_data.get("duration", 60),
            timezone=input_data.get("timezone", "UTC"),
            agenda=input_data.get("agenda", ""),
        )
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
    try:
        from app.external_comms.platforms.zoom import ZoomClient
        client = ZoomClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
        result = client.list_meetings(meeting_type=input_data.get("meeting_type", "scheduled"))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
    try:
        from app.external_comms.platforms.zoom import ZoomClient
        client = ZoomClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
        result = client.get_meeting(input_data["meeting_id"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
    try:
        from app.external_comms.platforms.zoom import ZoomClient
        client = ZoomClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
        result = client.delete_meeting(input_data["meeting_id"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="get_zoom_profile",
    description="Get Zoom profile.",
    action_sets=["zoom"],
    input_schema={},
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_zoom_profile(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.zoom import ZoomClient
        client = ZoomClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
        result = client.get_user_profile()
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="get_upcoming_zoom_meetings",
    description="Get upcoming meetings.",
    action_sets=["zoom"],
    input_schema={"page_size": {"type": "integer", "description": "Page size.", "example": 30}},
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_upcoming_zoom_meetings(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.zoom import ZoomClient
        client = ZoomClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
        result = client.get_upcoming_meetings(page_size=input_data.get("page_size", 30))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="get_live_zoom_meetings",
    description="Get live meetings.",
    action_sets=["zoom"],
    input_schema={},
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_live_zoom_meetings(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.zoom import ZoomClient
        client = ZoomClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
        result = client.get_live_meetings()
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="update_zoom_meeting",
    description="Update a meeting.",
    action_sets=["zoom"],
    input_schema={
        "meeting_id": {"type": "string", "description": "Meeting ID.", "example": "123"},
        "topic": {"type": "string", "description": "Topic.", "example": "New Topic"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def update_zoom_meeting(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.zoom import ZoomClient
        client = ZoomClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
        result = client.update_meeting(
            input_data["meeting_id"],
            topic=input_data.get("topic"),
            start_time=input_data.get("start_time"),
            duration=input_data.get("duration"),
            timezone=input_data.get("timezone"),
            agenda=input_data.get("agenda"),
            password=input_data.get("password"),
            settings=input_data.get("settings"),
        )
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="get_zoom_meeting_invitation",
    description="Get invitation.",
    action_sets=["zoom"],
    input_schema={"meeting_id": {"type": "string", "description": "Meeting ID.", "example": "123"}},
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_zoom_meeting_invitation(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.zoom import ZoomClient
        client = ZoomClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
        result = client.get_meeting_invitation(input_data["meeting_id"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="list_zoom_users",
    description="List users.",
    action_sets=["zoom"],
    input_schema={"page_size": {"type": "integer", "description": "Page size.", "example": 30}},
    output_schema={"status": {"type": "string", "example": "success"}},
)
def list_zoom_users(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.zoom import ZoomClient
        client = ZoomClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Zoom credential. Use /zoom login first."}
        result = client.list_users(page_size=input_data.get("page_size", 30))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
