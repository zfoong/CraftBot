from core.action.action_framework.registry import action


@action(
    name="list_drive_files",
    description="List files in a Google Drive folder.",
    action_sets=["google_workspace"],
    input_schema={
        "folder_id": {"type": "string", "description": "Google Drive folder ID.", "example": "root"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def list_drive_files(input_data: dict) -> dict:
    from core.external_libraries.google_workspace.external_app_library import GoogleWorkspaceAppLibrary
    GoogleWorkspaceAppLibrary.initialize()
    creds = GoogleWorkspaceAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Google credential. Use /google login first."}
    cred = creds[0]
    from core.external_libraries.google_workspace.helpers.google_drive_helpers import list_drive_files as _list
    result = _list(cred.token, input_data["folder_id"])
    return {"status": "success", "result": result}


@action(
    name="create_drive_folder",
    description="Create a new folder in Google Drive.",
    action_sets=["google_workspace"],
    input_schema={
        "name": {"type": "string", "description": "Folder name.", "example": "Project Files"},
        "parent_folder_id": {"type": "string", "description": "Optional parent folder ID.", "example": ""},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def create_drive_folder(input_data: dict) -> dict:
    from core.external_libraries.google_workspace.external_app_library import GoogleWorkspaceAppLibrary
    GoogleWorkspaceAppLibrary.initialize()
    creds = GoogleWorkspaceAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Google credential. Use /google login first."}
    cred = creds[0]
    from core.external_libraries.google_workspace.helpers.google_drive_helpers import create_drive_folder as _create
    result = _create(cred.token, input_data["name"],
                     parent_folder_id=input_data.get("parent_folder_id"))
    return {"status": "success", "result": result}


@action(
    name="move_drive_file",
    description="Move a file to a different Google Drive folder.",
    action_sets=["google_workspace"],
    input_schema={
        "file_id": {"type": "string", "description": "File ID to move.", "example": "abc123"},
        "destination_folder_id": {"type": "string", "description": "Destination folder ID.", "example": "def456"},
        "source_folder_id": {"type": "string", "description": "Current parent folder ID.", "example": "root"},
    },
    output_schema={"status": {"type": "string", "example": "success"}},
)
def move_drive_file(input_data: dict) -> dict:
    from core.external_libraries.google_workspace.external_app_library import GoogleWorkspaceAppLibrary
    GoogleWorkspaceAppLibrary.initialize()
    creds = GoogleWorkspaceAppLibrary.get_credential_store().get(input_data.get("user_id", "local"))
    if not creds:
        return {"status": "error", "message": "No Google credential. Use /google login first."}
    cred = creds[0]
    from core.external_libraries.google_workspace.helpers.google_drive_helpers import move_drive_file as _move
    result = _move(cred.token, input_data["file_id"],
                   add_parents=input_data["destination_folder_id"],
                   remove_parents=input_data.get("source_folder_id", ""))
    return {"status": "success", "result": result}
