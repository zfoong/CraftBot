from core.action.action_framework.registry import action


@action(
    name="get_linkedin_profile",
    description="Get the authenticated user's LinkedIn profile.",
    action_sets=["linkedin"],
    input_schema={},
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_linkedin_profile(input_data: dict) -> dict:
    from core.external_libraries.linkedin.external_app_library import LinkedInAppLibrary
    LinkedInAppLibrary.initialize()
    creds = LinkedInAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No LinkedIn credential. Use /linkedin login first."}
    cred = creds[0]
    from core.external_libraries.linkedin.helpers.linkedin_helpers import get_user_profile
    result = get_user_profile(cred.access_token)
    return {"status": "success", "result": result}


@action(
    name="create_linkedin_post",
    description="Create a text post on LinkedIn.",
    action_sets=["linkedin"],
    input_schema={
        "text": {"type": "string", "description": "Post text (max 3000 chars).", "example": "Excited to share..."},
        "visibility": {"type": "string", "description": "Visibility: PUBLIC, CONNECTIONS, or LOGGED_IN.", "example": "PUBLIC"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def create_linkedin_post(input_data: dict) -> dict:
    from core.external_libraries.linkedin.external_app_library import LinkedInAppLibrary
    LinkedInAppLibrary.initialize()
    creds = LinkedInAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No LinkedIn credential. Use /linkedin login first."}
    cred = creds[0]
    from core.external_libraries.linkedin.helpers.linkedin_helpers import create_text_post
    author_urn = cred.linkedin_id or f"urn:li:person:{cred.user_id}"
    result = create_text_post(cred.access_token, author_urn, input_data["text"],
                              visibility=input_data.get("visibility", "PUBLIC"))
    return {"status": "success", "result": result}


@action(
    name="search_linkedin_jobs",
    description="Search for job postings on LinkedIn.",
    action_sets=["linkedin"],
    input_schema={
        "keywords": {"type": "string", "description": "Job search keywords.", "example": "software engineer"},
        "location": {"type": "string", "description": "Optional location filter.", "example": ""},
        "count": {"type": "integer", "description": "Number of results.", "example": 25},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def search_linkedin_jobs(input_data: dict) -> dict:
    from core.external_libraries.linkedin.external_app_library import LinkedInAppLibrary
    LinkedInAppLibrary.initialize()
    creds = LinkedInAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No LinkedIn credential. Use /linkedin login first."}
    cred = creds[0]
    from core.external_libraries.linkedin.helpers.linkedin_helpers import search_jobs
    result = search_jobs(cred.access_token, input_data["keywords"],
                         location=input_data.get("location"),
                         count=input_data.get("count", 25))
    return {"status": "success", "result": result}


@action(
    name="get_linkedin_connections",
    description="Get the authenticated user's LinkedIn connections.",
    action_sets=["linkedin"],
    input_schema={
        "count": {"type": "integer", "description": "Number of connections to return.", "example": 50},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_linkedin_connections(input_data: dict) -> dict:
    from core.external_libraries.linkedin.external_app_library import LinkedInAppLibrary
    LinkedInAppLibrary.initialize()
    creds = LinkedInAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No LinkedIn credential. Use /linkedin login first."}
    cred = creds[0]
    from core.external_libraries.linkedin.helpers.linkedin_helpers import get_connections
    result = get_connections(cred.access_token, count=input_data.get("count", 50))
    return {"status": "success", "result": result}


@action(
    name="send_linkedin_message",
    description="Send a message to LinkedIn users.",
    action_sets=["linkedin"],
    input_schema={
        "recipient_urns": {"type": "array", "description": "List of recipient URNs (urn:li:person:xxx).", "example": []},
        "subject": {"type": "string", "description": "Message subject.", "example": "Hello"},
        "body": {"type": "string", "description": "Message body.", "example": "Hi, I wanted to connect..."},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def send_linkedin_message(input_data: dict) -> dict:
    from core.external_libraries.linkedin.external_app_library import LinkedInAppLibrary
    LinkedInAppLibrary.initialize()
    creds = LinkedInAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No LinkedIn credential. Use /linkedin login first."}
    cred = creds[0]
    from core.external_libraries.linkedin.helpers.linkedin_helpers import send_message
    sender_urn = cred.linkedin_id or f"urn:li:person:{cred.user_id}"
    result = send_message(cred.access_token, sender_urn, input_data["recipient_urns"],
                          input_data["subject"], input_data["body"])
    return {"status": "success", "result": result}
