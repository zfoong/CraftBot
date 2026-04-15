from agent_core import action

@action(
    name="write_file",
    description="Write or overwrite a text file with the provided content. Creates parent directories if they don't exist.",
    mode="CLI",
    action_sets=["core"],
    parallelizable=False,
    input_schema={
        "file_path": {
            "type": "string",
            "example": "/workspace/output.txt",
            "description": "Absolute path to the file to write."
        },
        "content": {
            "type": "string",
            "example": "Hello, World!",
            "description": "Content to write to the file."
        },
        "encoding": {
            "type": "string",
            "example": "utf-8",
            "description": "File encoding. Defaults to 'utf-8'."
        },
        "mode": {
            "type": "string",
            "example": "overwrite",
            "description": "Write mode: 'overwrite' or 'append'. Defaults to 'overwrite'."
        }
    },
    output_schema={
        "status": {
            "type": "string",
            "example": "success",
            "description": "'success' or 'error'."
        },
        "file_path": {
            "type": "string",
            "description": "Path to the written file."
        },
        "bytes_written": {
            "type": "integer",
            "description": "Number of bytes written."
        },
        "message": {
            "type": "string",
            "description": "Error message if status is 'error'."
        }
    },
    test_payload={
        "file_path": "/workspace/test_output.txt",
        "content": "Test content",
        "simulated_mode": True
    }
)
def write_file(input_data: dict) -> dict:
    import os

    simulated_mode = input_data.get('simulated_mode', False)

    if simulated_mode:
        return {
            'status': 'success',
            'file_path': input_data.get('file_path', '/workspace/test_output.txt'),
            'bytes_written': len(input_data.get('content', ''))
        }

    file_path = input_data.get('file_path', '')
    content = input_data.get('content', '')
    encoding = input_data.get('encoding', 'utf-8')
    write_mode = input_data.get('mode', 'overwrite').lower()

    if not file_path:
        return {'status': 'error', 'file_path': '', 'bytes_written': 0, 'message': 'file_path is required.'}

    if write_mode not in ('overwrite', 'append'):
        return {'status': 'error', 'file_path': '', 'bytes_written': 0, 'message': "mode must be 'overwrite' or 'append'."}

    # Resolve path to prevent traversal attacks (resolve parent since file may not exist yet)
    parent_dir = os.path.dirname(os.path.abspath(file_path))
    resolved_parent = os.path.realpath(parent_dir) if os.path.exists(parent_dir) else os.path.abspath(parent_dir)
    resolved_path = os.path.join(resolved_parent, os.path.basename(file_path))

    # Block writes to sensitive directories
    _BLOCKED_DIRS = ('.credentials', '.ssh', '.gnupg', '.aws', '.env')
    path_parts = resolved_path.replace('\\', '/').split('/')
    if any(part in _BLOCKED_DIRS for part in path_parts):
        return {'status': 'error', 'file_path': '', 'bytes_written': 0, 'message': f'Access denied: cannot write to restricted location.'}

    try:
        # Create parent directories if needed
        if resolved_parent:
            os.makedirs(resolved_parent, exist_ok=True)

        file_mode = 'w' if write_mode == 'overwrite' else 'a'
        with open(resolved_path, file_mode, encoding=encoding) as f:
            bytes_written = f.write(content)

        return {
            'status': 'success',
            'file_path': file_path,
            'bytes_written': bytes_written
        }
    except Exception as e:
        return {'status': 'error', 'file_path': '', 'bytes_written': 0, 'message': str(e)}
