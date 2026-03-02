from agent_core import action


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
    try:
        from app.external_comms.platforms.recall import RecallClient
        client = RecallClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Recall credential. Use /recall login first."}
        result = client.create_bot(input_data["meeting_url"], bot_name=input_data.get("bot_name", "Meeting Assistant"))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
    try:
        from app.external_comms.platforms.recall import RecallClient
        client = RecallClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Recall credential. Use /recall login first."}
        result = client.get_bot(input_data["bot_id"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
    try:
        from app.external_comms.platforms.recall import RecallClient
        client = RecallClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Recall credential. Use /recall login first."}
        result = client.get_transcript(input_data["bot_id"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


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
    try:
        from app.external_comms.platforms.recall import RecallClient
        client = RecallClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Recall credential. Use /recall login first."}
        result = client.leave_meeting(input_data["bot_id"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="list_meeting_bots",
    description="List bots.",
    action_sets=["recall"],
    input_schema={"page_size": {"type": "integer", "description": "Page size.", "example": 50}},
    output_schema={"status": {"type": "string", "example": "success"}},
)
def list_meeting_bots(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.recall import RecallClient
        client = RecallClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Recall credential. Use /recall login first."}
        result = client.list_bots(page_size=input_data.get("page_size", 50))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="delete_meeting_bot",
    description="Delete bot.",
    action_sets=["recall"],
    input_schema={"bot_id": {"type": "string", "description": "Bot ID.", "example": "abc"}},
    output_schema={"status": {"type": "string", "example": "success"}},
)
def delete_meeting_bot(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.recall import RecallClient
        client = RecallClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Recall credential. Use /recall login first."}
        result = client.delete_bot(input_data["bot_id"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="get_meeting_recording",
    description="Get recording.",
    action_sets=["recall"],
    input_schema={"bot_id": {"type": "string", "description": "Bot ID.", "example": "abc"}},
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_meeting_recording(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.recall import RecallClient
        client = RecallClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Recall credential. Use /recall login first."}
        result = client.get_recording(input_data["bot_id"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="send_meeting_chat_message",
    description="Send chat.",
    action_sets=["recall"],
    input_schema={
        "bot_id": {"type": "string", "description": "Bot ID.", "example": "abc"},
        "message": {"type": "string", "description": "Message.", "example": "Hi"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def send_meeting_chat_message(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.recall import RecallClient
        client = RecallClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Recall credential. Use /recall login first."}
        result = client.send_chat_message(input_data["bot_id"], input_data["message"])
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@action(
    name="speak_in_meeting",
    description="Speak in meeting (audio).",
    action_sets=["recall"],
    input_schema={
        "bot_id": {"type": "string", "description": "Bot ID.", "example": "abc"},
        "audio_data": {"type": "string", "description": "Base64 audio.", "example": "UklGR..."},
        "audio_format": {"type": "string", "description": "Format.", "example": "wav"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def speak_in_meeting(input_data: dict) -> dict:
    try:
        from app.external_comms.platforms.recall import RecallClient
        client = RecallClient()
        if not client.has_credentials():
            return {"status": "error", "message": "No Recall credential. Use /recall login first."}
        result = client.output_audio(input_data["bot_id"], input_data["audio_data"], audio_format=input_data.get("audio_format", "wav"))
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
