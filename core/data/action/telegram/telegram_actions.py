from core.action.action_framework.registry import action


@action(
    name="send_telegram_message",
    description="Send a text message to a Telegram chat via bot.",
    action_sets=["telegram"],
    input_schema={
        "chat_id": {"type": "string", "description": "Telegram chat ID or @username.", "example": "123456789"},
        "text": {"type": "string", "description": "Message text to send.", "example": "Hello!"},
        "parse_mode": {"type": "string", "description": "Optional parse mode: HTML or Markdown.", "example": "HTML"},
    },
    output_schema={
        "status": {"type": "string", "example": "success"},
        "message": {"type": "string", "example": "Message sent"},
    },
)
def send_telegram_message(input_data: dict) -> dict:
    from core.external_libraries.telegram.external_app_library import TelegramAppLibrary
    TelegramAppLibrary.initialize()
    creds = [c for c in TelegramAppLibrary.get_credential_store().get(
        input_data.get("user_id", "local")) if c.connection_type == "bot_api"]
    if not creds:
        return {"status": "error", "message": "No Telegram bot credential. Use /telegram login first."}
    cred = creds[0]
    from core.external_libraries.telegram.helpers.telegram_helpers import send_message
    result = send_message(cred.bot_token, input_data["chat_id"], input_data["text"],
                          parse_mode=input_data.get("parse_mode"))
    return {"status": "success", "result": result}


@action(
    name="send_telegram_photo",
    description="Send a photo to a Telegram chat via bot.",
    action_sets=["telegram"],
    input_schema={
        "chat_id": {"type": "string", "description": "Telegram chat ID.", "example": "123456789"},
        "photo": {"type": "string", "description": "URL or file_id of the photo.", "example": "https://example.com/photo.jpg"},
        "caption": {"type": "string", "description": "Optional photo caption.", "example": "Check this out"},
    },
    output_schema={
        "status": {"type": "string", "example": "success"},
    },
)
def send_telegram_photo(input_data: dict) -> dict:
    from core.external_libraries.telegram.external_app_library import TelegramAppLibrary
    TelegramAppLibrary.initialize()
    creds = [c for c in TelegramAppLibrary.get_credential_store().get(
        input_data.get("user_id", "local")) if c.connection_type == "bot_api"]
    if not creds:
        return {"status": "error", "message": "No Telegram bot credential. Use /telegram login first."}
    cred = creds[0]
    from core.external_libraries.telegram.helpers.telegram_helpers import send_photo
    result = send_photo(cred.bot_token, input_data["chat_id"], input_data["photo"],
                        caption=input_data.get("caption"))
    return {"status": "success", "result": result}


@action(
    name="get_telegram_updates",
    description="Get incoming updates (messages) for the Telegram bot.",
    action_sets=["telegram"],
    input_schema={
        "limit": {"type": "integer", "description": "Max number of updates to retrieve.", "example": 10},
        "offset": {"type": "integer", "description": "Update offset for pagination.", "example": 0},
    },
    output_schema={
        "status": {"type": "string", "example": "success"},
        "updates": {"type": "array", "description": "List of update objects."},
    },
)
def get_telegram_updates(input_data: dict) -> dict:
    from core.external_libraries.telegram.external_app_library import TelegramAppLibrary
    TelegramAppLibrary.initialize()
    creds = [c for c in TelegramAppLibrary.get_credential_store().get(
        input_data.get("user_id", "local")) if c.connection_type == "bot_api"]
    if not creds:
        return {"status": "error", "message": "No Telegram bot credential. Use /telegram login first."}
    cred = creds[0]
    from core.external_libraries.telegram.helpers.telegram_helpers import get_updates
    result = get_updates(cred.bot_token, limit=input_data.get("limit", 100),
                         offset=input_data.get("offset"))
    return {"status": "success", "result": result}


@action(
    name="get_telegram_chat",
    description="Get information about a Telegram chat.",
    action_sets=["telegram"],
    input_schema={
        "chat_id": {"type": "string", "description": "Chat ID or @username.", "example": "123456789"},
    },
    output_schema={
        "status": {"type": "string", "example": "success"},
    },
)
def get_telegram_chat(input_data: dict) -> dict:
    from core.external_libraries.telegram.external_app_library import TelegramAppLibrary
    TelegramAppLibrary.initialize()
    creds = [c for c in TelegramAppLibrary.get_credential_store().get(
        input_data.get("user_id", "local")) if c.connection_type == "bot_api"]
    if not creds:
        return {"status": "error", "message": "No Telegram bot credential. Use /telegram login first."}
    cred = creds[0]
    from core.external_libraries.telegram.helpers.telegram_helpers import get_chat
    result = get_chat(cred.bot_token, input_data["chat_id"])
    return {"status": "success", "result": result}


@action(
    name="search_telegram_contact",
    description="Search for a Telegram contact by name from bot's recent chat history.",
    action_sets=["telegram"],
    input_schema={
        "name": {"type": "string", "description": "Contact name to search for.", "example": "John"},
    },
    output_schema={
        "status": {"type": "string", "example": "success"},
    },
)
def search_telegram_contact(input_data: dict) -> dict:
    from core.external_libraries.telegram.external_app_library import TelegramAppLibrary
    TelegramAppLibrary.initialize()
    creds = [c for c in TelegramAppLibrary.get_credential_store().get(
        input_data.get("user_id", "local")) if c.connection_type == "bot_api"]
    if not creds:
        return {"status": "error", "message": "No Telegram bot credential. Use /telegram login first."}
    cred = creds[0]
    from core.external_libraries.telegram.helpers.telegram_helpers import search_contact
    result = search_contact(cred.bot_token, input_data["name"])
    return {"status": "success", "result": result}
