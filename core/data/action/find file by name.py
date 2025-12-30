from core.action.action_framework.registry import action

@action(
    name="find file by name",
    description="Finds files by name or pattern across the system. Supports wildcards, relative paths, and recursive search.",
    mode="CLI",
    platforms=["linux", "darwin"],
    input_schema={
        "pattern": {
            "type": "string",
            "example": "*.pdf",
            "description": "The file name or glob pattern to match. Supports wildcards like * and ?"
        },
        "recursive": {
            "type": "boolean",
            "example": True,
            "description": "Whether to search directories recursively. Default is true."
        }
    },
    output_schema={
        "status": {
            "type": "string",
            "example": "success"
        },
        "matches": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "example": [
                "~/Documents/file1.pdf",
                "~/Documents/reports/file2.pdf"
            ]
        },
        "message": {
            "type": "string",
            "example": "No files matched."
        }
    },
    test_payload={
        "pattern": "*.pdf",
        "recursive": True,
        "simulated_mode": True
    }
)
def find_file_by_name(input_data: dict) -> dict:
    import json, os, fnmatch

    pattern = input_data.get('pattern', '').strip()
    recursive = bool(input_data.get('recursive', True))

    if not pattern:
        return {'status': 'error', 'matches': [], 'message': 'Pattern is required.'}
        exit()

    pattern = os.path.expanduser(pattern)
    pattern = os.path.normpath(pattern)

    # Determine base directory and file pattern
    if os.path.isabs(pattern) or os.sep in pattern:
        base_dir = os.path.dirname(pattern) or os.path.expanduser('~')
        file_pattern = os.path.basename(pattern)
    else:
        base_dir = os.path.expanduser('~')
        file_pattern = pattern

    matches = []
    for root, dirs, files in os.walk(base_dir):
        try:
            for name in files:
                if fnmatch.fnmatch(name, file_pattern):
                    matches.append(os.path.abspath(os.path.join(root, name)))
        except PermissionError:
            continue
        if not recursive:
            break

    return {
        'status': 'success',
        'matches': matches,
        'message': '' if matches else f"No files matching '{file_pattern}' were found."
    }

@action(
    name="find file by name",
    description="Finds files by name or pattern across the system. Supports wildcards, relative paths, and recursive search.",
    mode="CLI",
    platforms=["windows"],
    input_schema={
        "pattern": {
            "type": "string",
            "example": "*.pdf",
            "description": "The file name or glob pattern to match. Supports wildcards like * and ?"
        },
        "recursive": {
            "type": "boolean",
            "example": True,
            "description": "Whether to search directories recursively. Default is true."
        }
    },
    output_schema={
        "status": {
            "type": "string",
            "example": "success"
        },
        "matches": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "example": [
                "~/Documents/file1.pdf",
                "~/Documents/reports/file2.pdf"
            ]
        },
        "message": {
            "type": "string",
            "example": "No files matched."
        }
    },
    test_payload={
        "pattern": "*.pdf",
        "recursive": True,
        "simulated_mode": True
    }
)
def find_file_by_name_windows(input_data: dict) -> dict:
    import json, os, fnmatch

    pattern = input_data.get('pattern', '').strip()
    recursive = bool(input_data.get('recursive', True))

    if not pattern:
        return {'status': 'error', 'matches': [], 'message': 'Pattern is required.'}
        exit()

    pattern = pattern.replace('/', '\\')
    pattern = os.path.expanduser(pattern)
    pattern = os.path.normpath(pattern)

    if os.path.isabs(pattern) or '\\' in pattern:
        base_dir = os.path.dirname(pattern) or os.path.expanduser('~')
        file_pattern = os.path.basename(pattern)
    else:
        base_dir = os.path.expanduser('~')
        file_pattern = pattern

    matches = []
    for root, dirs, files in os.walk(base_dir):
        try:
            for name in files:
                if fnmatch.fnmatch(name, file_pattern):
                    matches.append(os.path.abspath(os.path.join(root, name)))
        except PermissionError:
            continue
        if not recursive:
            break

    return {
        'status': 'success',
        'matches': matches,
        'message': '' if matches else f"No files matching '{file_pattern}' were found."
    }