from core.action.action_framework.registry import action


@action(
    name="search_notion",
    description="Search Notion workspace for pages and databases.",
    action_sets=["notion"],
    input_schema={
        "query": {"type": "string", "description": "Search query.", "example": "meeting notes"},
        "filter_type": {"type": "string", "description": "Optional: 'page' or 'database'.", "example": "page"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def search_notion(input_data: dict) -> dict:
    from core.external_libraries.notion.external_app_library import NotionAppLibrary
    NotionAppLibrary.initialize()
    creds = NotionAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Notion credential. Use /notion login first."}
    cred = creds[0]
    from core.external_libraries.notion.helpers.notion_helpers import search_notion as _search
    result = _search(cred.token, input_data["query"], filter_type=input_data.get("filter_type"))
    return {"status": "success", "result": result}


@action(
    name="get_notion_page",
    description="Get a Notion page by ID.",
    action_sets=["notion"],
    input_schema={
        "page_id": {"type": "string", "description": "Notion page ID.", "example": "abc123"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def get_notion_page(input_data: dict) -> dict:
    from core.external_libraries.notion.external_app_library import NotionAppLibrary
    NotionAppLibrary.initialize()
    creds = NotionAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Notion credential. Use /notion login first."}
    cred = creds[0]
    from core.external_libraries.notion.helpers.notion_helpers import get_page
    result = get_page(cred.token, input_data["page_id"])
    return {"status": "success", "result": result}


@action(
    name="create_notion_page",
    description="Create a new page in Notion.",
    action_sets=["notion"],
    input_schema={
        "parent_id": {"type": "string", "description": "Parent page or database ID.", "example": "abc123"},
        "parent_type": {"type": "string", "description": "'page_id' or 'database_id'.", "example": "page_id"},
        "properties": {"type": "object", "description": "Page properties.", "example": {"title": [{"text": {"content": "New Page"}}]}},
        "children": {"type": "array", "description": "Optional content blocks.", "example": []},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def create_notion_page(input_data: dict) -> dict:
    from core.external_libraries.notion.external_app_library import NotionAppLibrary
    NotionAppLibrary.initialize()
    creds = NotionAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Notion credential. Use /notion login first."}
    cred = creds[0]
    from core.external_libraries.notion.helpers.notion_helpers import create_page
    result = create_page(cred.token, input_data["parent_id"], input_data["parent_type"],
                         input_data["properties"], children=input_data.get("children"))
    return {"status": "success", "result": result}


@action(
    name="query_notion_database",
    description="Query a Notion database with optional filters and sorts.",
    action_sets=["notion"],
    input_schema={
        "database_id": {"type": "string", "description": "Database ID.", "example": "abc123"},
        "filter": {"type": "object", "description": "Optional Notion filter object.", "example": {}},
        "sorts": {"type": "array", "description": "Optional sort array.", "example": []},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def query_notion_database(input_data: dict) -> dict:
    from core.external_libraries.notion.external_app_library import NotionAppLibrary
    NotionAppLibrary.initialize()
    creds = NotionAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Notion credential. Use /notion login first."}
    cred = creds[0]
    from core.external_libraries.notion.helpers.notion_helpers import query_database
    result = query_database(cred.token, input_data["database_id"],
                            filter_obj=input_data.get("filter"), sorts=input_data.get("sorts"))
    return {"status": "success", "result": result}


@action(
    name="update_notion_page",
    description="Update a Notion page's properties.",
    action_sets=["notion"],
    input_schema={
        "page_id": {"type": "string", "description": "Page ID to update.", "example": "abc123"},
        "properties": {"type": "object", "description": "Properties to update.", "example": {}},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def update_notion_page(input_data: dict) -> dict:
    from core.external_libraries.notion.external_app_library import NotionAppLibrary
    NotionAppLibrary.initialize()
    creds = NotionAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Notion credential. Use /notion login first."}
    cred = creds[0]
    from core.external_libraries.notion.helpers.notion_helpers import update_page
    result = update_page(cred.token, input_data["page_id"], input_data["properties"])
    return {"status": "success", "result": result}
