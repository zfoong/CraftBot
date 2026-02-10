from core.action.action_framework.registry import action


@action(
    name="create_recall_bot",
    description="Create a Recall.ai bot to join a meeting and record/transcribe.",
    action_sets=["recall"],
    input_schema={
        "meeting_url": {"type": "string", "description": "Meeting URL (Zoom, Google Meet, Teams).", "example": "https://meet.google.com/abc-defg-hij"},
        "bot_name": {"type": "string", "description": "Display name for the bot.", "example": "Meeting Assistant"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def create_recall_bot(input_data: dict) -> dict:
    from core.external_libraries.recall.external_app_library import RecallAppLibrary
    RecallAppLibrary.initialize()
    creds = RecallAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Recall credential. Use /recall login first."}
    cred = creds[0]
    from core.external_libraries.recall.helpers.recall_helpers import create_bot
    result = create_bot(cred.api_key, input_data["meeting_url"],
                        bot_name=input_data.get("bot_name", "Meeting Assistant"),
                        region=cred.region)
    return {"status": "success", "result": result}


@action(
    name="get_recall_bot",
    description="Get status and details of a Recall.ai bot.",
    action_sets=["recall"],
    input_schema={
        "bot_id": {"type": "string", "description": "Recall bot ID.", "example": "abc-123"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_recall_bot(input_data: dict) -> dict:
    from core.external_libraries.recall.external_app_library import RecallAppLibrary
    RecallAppLibrary.initialize()
    creds = RecallAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Recall credential. Use /recall login first."}
    cred = creds[0]
    from core.external_libraries.recall.helpers.recall_helpers import get_bot
    result = get_bot(cred.api_key, input_data["bot_id"], region=cred.region)
    return {"status": "success", "result": result}


@action(
    name="get_recall_transcript",
    description="Get the meeting transcript from a Recall.ai bot.",
    action_sets=["recall"],
    input_schema={
        "bot_id": {"type": "string", "description": "Recall bot ID.", "example": "abc-123"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_recall_transcript(input_data: dict) -> dict:
    from core.external_libraries.recall.external_app_library import RecallAppLibrary
    RecallAppLibrary.initialize()
    creds = RecallAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Recall credential. Use /recall login first."}
    cred = creds[0]
    from core.external_libraries.recall.helpers.recall_helpers import get_transcript
    result = get_transcript(cred.api_key, input_data["bot_id"], region=cred.region)
    return {"status": "success", "result": result}


@action(
    name="recall_leave_meeting",
    description="Make a Recall.ai bot leave the meeting.",
    action_sets=["recall"],
    input_schema={
        "bot_id": {"type": "string", "description": "Recall bot ID.", "example": "abc-123"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def recall_leave_meeting(input_data: dict) -> dict:
    from core.external_libraries.recall.external_app_library import RecallAppLibrary
    RecallAppLibrary.initialize()
    creds = RecallAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Recall credential. Use /recall login first."}
    cred = creds[0]
    from core.external_libraries.recall.helpers.recall_helpers import leave_meeting
    result = leave_meeting(cred.api_key, input_data["bot_id"], region=cred.region)
    return {"status": "success", "result": result}
