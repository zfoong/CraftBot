from core.action.action_framework.registry import action


@action(
    name="send_whatsapp_message",
    description="Send a text message via WhatsApp Business API.",
    action_sets=["whatsapp"],
    input_schema={
        "to": {"type": "string", "description": "Recipient phone number with country code.", "example": "1234567890"},
        "message": {"type": "string", "description": "Message text.", "example": "Hello!"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def send_whatsapp_message(input_data: dict) -> dict:
    from core.external_libraries.whatsapp.external_app_library import WhatsAppAppLibrary
    WhatsAppAppLibrary.initialize()
    creds = [c for c in WhatsAppAppLibrary.get_credential_store().get(
        input_data.get("user_id", "local")) if c.connection_type == "business_api"]
    if not creds:
        return {"status": "error", "message": "No WhatsApp Business credential. Use /whatsapp login first."}
    cred = creds[0]
    from core.external_libraries.whatsapp.helpers.whatsapp_helpers import send_text_message
    result = send_text_message(cred.access_token, cred.phone_number_id,
                               input_data["to"], input_data["message"])
    return {"status": "success", "result": result}


@action(
    name="send_whatsapp_media",
    description="Send a media message (image, video, audio, document) via WhatsApp.",
    action_sets=["whatsapp"],
    input_schema={
        "to": {"type": "string", "description": "Recipient phone number with country code.", "example": "1234567890"},
        "media_type": {"type": "string", "description": "Type: image, video, audio, document.", "example": "image"},
        "media_url": {"type": "string", "description": "Public URL of the media.", "example": "https://example.com/photo.jpg"},
        "caption": {"type": "string", "description": "Optional caption.", "example": "Check this out"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def send_whatsapp_media(input_data: dict) -> dict:
    from core.external_libraries.whatsapp.external_app_library import WhatsAppAppLibrary
    WhatsAppAppLibrary.initialize()
    creds = [c for c in WhatsAppAppLibrary.get_credential_store().get(
        input_data.get("user_id", "local")) if c.connection_type == "business_api"]
    if not creds:
        return {"status": "error", "message": "No WhatsApp Business credential. Use /whatsapp login first."}
    cred = creds[0]
    from core.external_libraries.whatsapp.helpers.whatsapp_helpers import send_media_message
    result = send_media_message(cred.access_token, cred.phone_number_id,
                                input_data["to"], input_data["media_type"],
                                media_url=input_data.get("media_url"),
                                caption=input_data.get("caption"))
    return {"status": "success", "result": result}


@action(
    name="send_whatsapp_template",
    description="Send a template message via WhatsApp Business API.",
    action_sets=["whatsapp"],
    input_schema={
        "to": {"type": "string", "description": "Recipient phone number.", "example": "1234567890"},
        "template_name": {"type": "string", "description": "Approved template name.", "example": "hello_world"},
        "language_code": {"type": "string", "description": "Language code.", "example": "en_US"},
        "components": {"type": "array", "description": "Optional template components.", "example": []},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def send_whatsapp_template(input_data: dict) -> dict:
    from core.external_libraries.whatsapp.external_app_library import WhatsAppAppLibrary
    WhatsAppAppLibrary.initialize()
    creds = [c for c in WhatsAppAppLibrary.get_credential_store().get(
        input_data.get("user_id", "local")) if c.connection_type == "business_api"]
    if not creds:
        return {"status": "error", "message": "No WhatsApp Business credential. Use /whatsapp login first."}
    cred = creds[0]
    from core.external_libraries.whatsapp.helpers.whatsapp_helpers import send_template_message
    result = send_template_message(cred.access_token, cred.phone_number_id,
                                   input_data["to"], input_data["template_name"],
                                   language_code=input_data.get("language_code", "en_US"),
                                   components=input_data.get("components"))
    return {"status": "success", "result": result}


@action(
    name="get_whatsapp_profile",
    description="Get the WhatsApp Business profile.",
    action_sets=["whatsapp"],
    input_schema={},
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_whatsapp_profile(input_data: dict) -> dict:
    from core.external_libraries.whatsapp.external_app_library import WhatsAppAppLibrary
    WhatsAppAppLibrary.initialize()
    creds = [c for c in WhatsAppAppLibrary.get_credential_store().get(
        input_data.get("user_id", "local")) if c.connection_type == "business_api"]
    if not creds:
        return {"status": "error", "message": "No WhatsApp Business credential. Use /whatsapp login first."}
    cred = creds[0]
    from core.external_libraries.whatsapp.helpers.whatsapp_helpers import get_business_profile
    result = get_business_profile(cred.access_token, cred.phone_number_id)
    return {"status": "success", "result": result}
