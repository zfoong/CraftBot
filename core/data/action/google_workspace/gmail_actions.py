from core.action.action_framework.registry import action


@action(
    name="send_gmail",
    description="Send an email via Gmail.",
    action_sets=["google_workspace"],
    input_schema={
        "to": {"type": "string", "description": "Recipient email address.", "example": "user@example.com"},
        "subject": {"type": "string", "description": "Email subject.", "example": "Meeting Follow-up"},
        "body": {"type": "string", "description": "Email body text.", "example": "Hi, here are the notes..."},
        "attachments": {"type": "array", "description": "Optional list of file paths to attach.", "example": []},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def send_gmail(input_data: dict) -> dict:
    from core.external_libraries.google_workspace.external_app_library import GoogleWorkspaceAppLibrary
    GoogleWorkspaceAppLibrary.initialize()
    creds = GoogleWorkspaceAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Google credential. Use /google login first."}
    cred = creds[0]
    from core.external_libraries.google_workspace.helpers.google_helpers import encode_email, send_email_oauth2
    encoded = encode_email(input_data["to"], cred.email, input_data["subject"],
                           input_data["body"], attachments=input_data.get("attachments"))
    success = send_email_oauth2(cred.token, encoded)
    if success:
        return {"status": "success", "message": "Email sent."}
    return {"status": "error", "message": "Failed to send email."}


@action(
    name="list_gmail",
    description="List recent emails from Gmail inbox.",
    action_sets=["google_workspace"],
    input_schema={
        "count": {"type": "integer", "description": "Number of recent emails to list.", "example": 5},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def list_gmail(input_data: dict) -> dict:
    from core.external_libraries.google_workspace.external_app_library import GoogleWorkspaceAppLibrary
    GoogleWorkspaceAppLibrary.initialize()
    creds = GoogleWorkspaceAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Google credential. Use /google login first."}
    cred = creds[0]
    from core.external_libraries.google_workspace.helpers.google_helpers import list_recent_emails
    result = list_recent_emails(cred.token, n=input_data.get("count", 5))
    return {"status": "success", "result": result}


@action(
    name="get_gmail",
    description="Get details of a specific Gmail message by ID.",
    action_sets=["google_workspace"],
    input_schema={
        "message_id": {"type": "string", "description": "Gmail message ID.", "example": "18abc123def"},
        "full_body": {"type": "boolean", "description": "Whether to include full email body.", "example": False},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_gmail(input_data: dict) -> dict:
    from core.external_libraries.google_workspace.external_app_library import GoogleWorkspaceAppLibrary
    GoogleWorkspaceAppLibrary.initialize()
    creds = GoogleWorkspaceAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Google credential. Use /google login first."}
    cred = creds[0]
    from core.external_libraries.google_workspace.helpers.google_helpers import get_email_details
    result = get_email_details(cred.token, input_data["message_id"],
                               full_body=input_data.get("full_body", False))
    return {"status": "success", "result": result}


@action(
    name="read_top_emails",
    description="Read the top N recent emails with details.",
    action_sets=["google_workspace"],
    input_schema={
        "count": {"type": "integer", "description": "Number of emails to read.", "example": 5},
        "full_body": {"type": "boolean", "description": "Include full body text.", "example": False},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def read_top_emails(input_data: dict) -> dict:
    from core.external_libraries.google_workspace.external_app_library import GoogleWorkspaceAppLibrary
    GoogleWorkspaceAppLibrary.initialize()
    creds = GoogleWorkspaceAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Google credential. Use /google login first."}
    cred = creds[0]
    from core.external_libraries.google_workspace.helpers.google_helpers import read_top_n_emails
    result = read_top_n_emails(cred.token, n=input_data.get("count", 5),
                               full_body=input_data.get("full_body", False))
    return {"status": "success", "result": result}
