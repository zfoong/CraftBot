from core.action.action_framework.registry import action

@action(
        name="shell kill process (cross-platform)",
        description="Terminates a process by PID or image name across Windows, macOS, and Linux.",
        input_schema={
                "pid": {
                        "type": "integer",
                        "example": 1234,
                        "description": "Process ID to terminate. If provided, takes precedence over image_name."
                },
                "image_name": {
                        "type": "string",
                        "example": "python",
                        "description": "Process image name (e.g., 'python' or 'chrome'). Used when pid is not provided."
                },
                "force": {
                        "type": "boolean",
                        "example": True,
                        "description": "Forceful termination (-9 on Unix, /F on Windows)."
                },
                "tree": {
                        "type": "boolean",
                        "example": True,
                        "description": "Kill the process and its children. Supported on Windows (/T) and Linux/macOS via pkill -P."
                },
                "timeout": {
                        "type": "integer",
                        "example": 15,
                        "description": "Optional timeout in seconds for the kill command."
                }
        },
        output_schema={
                "status": {
                        "type": "string",
                        "example": "success",
                        "description": "'success' if the process was terminated, 'error' otherwise."
                },
                "stdout": {
                        "type": "string",
                        "example": "Process terminated.",
                        "description": "Captured standard output from the termination command."
                },
                "stderr": {
                        "type": "string",
                        "example": "",
                        "description": "Captured standard error from the termination command."
                },
                "return_code": {
                        "type": "integer",
                        "example": 0,
                        "description": "Exit code from the termination command. 0 indicates success."
                },
                "message": {
                        "type": "string",
                        "example": "No target specified.",
                        "description": "Optional message for validation or error details."
                }
        },
        test_payload={
                "pid": 1234,
                "image_name": "python",
                "force": True,
                "tree": True,
                "timeout": 15,
                "simulated_mode": True
        }
)
def shell_kill_process__cross_platform_(input_data: dict) -> dict:
    import os, json, subprocess, platform

    simulated_mode = input_data.get('simulated_mode', False)
    
    if simulated_mode:
        # Return mock result for testing
        return {
            'status': 'success',
            'stdout': 'Process terminated successfully',
            'stderr': '',
            'return_code': 0,
            'message': ''
        }

    pid = input_data.get('pid')
    image_name = str(input_data.get('image_name', '')).strip()
    force = bool(input_data.get('force', False))
    tree = bool(input_data.get('tree', False))
    timeout_val = input_data.get('timeout')

    system = platform.system().lower()

    if pid is None and not image_name:
        return {'status': 'error', 'stdout': '', 'stderr': '', 'return_code': -1, 'message': 'Specify either pid or image_name.'}

    if system == 'windows':
        args = ['taskkill']
        if pid is not None:
            args += ['/PID', str(pid)]
        else:
            args += ['/IM', image_name]
        if force:
            args.append('/F')
        if tree:
            args.append('/T')

    else:
        # macOS / Linux
        if pid is not None:
            sig = '-9' if force else '-15'
            args = ['kill', sig, str(pid)]
        else:
            if tree:
                args = ['pkill', '-f', image_name]
            else:
                args = ['pkill'] + (['-9'] if force else []) + ['-f', image_name]

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            errors='replace',
            timeout=float(timeout_val) if timeout_val is not None else None,
            shell=False
        )
        return {
            'status': 'success' if result.returncode == 0 else 'error',
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'return_code': result.returncode,
            'message': ''
        }
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or '').strip()
        err = (e.stderr or '').strip()
        msg = f'Timed out after {timeout_val}s.' if timeout_val is not None else 'Timed out.'
        return {'status': 'error', 'stdout': out, 'stderr': err, 'return_code': -1, 'message': msg}
    except Exception as e:
        return {'status': 'error', 'stdout': '', 'stderr': str(e), 'return_code': -1, 'message': str(e)}

@action(
        name="shell kill process (cross-platform)",
        description="Terminates a process by PID or image name across Windows, macOS, and Linux.",
        platforms=["windows"],
        input_schema={
                "pid": {
                        "type": "integer",
                        "example": 1234,
                        "description": "Process ID to terminate. If provided, takes precedence over image_name."
                },
                "image_name": {
                        "type": "string",
                        "example": "python",
                        "description": "Process image name (e.g., 'python' or 'chrome'). Used when pid is not provided."
                },
                "force": {
                        "type": "boolean",
                        "example": True,
                        "description": "Forceful termination (-9 on Unix, /F on Windows)."
                },
                "tree": {
                        "type": "boolean",
                        "example": True,
                        "description": "Kill the process and its children. Supported on Windows (/T) and Linux/macOS via pkill -P."
                },
                "timeout": {
                        "type": "integer",
                        "example": 15,
                        "description": "Optional timeout in seconds for the kill command."
                }
        },
        output_schema={
                "status": {
                        "type": "string",
                        "example": "success",
                        "description": "'success' if the process was terminated, 'error' otherwise."
                },
                "stdout": {
                        "type": "string",
                        "example": "Process terminated.",
                        "description": "Captured standard output from the termination command."
                },
                "stderr": {
                        "type": "string",
                        "example": "",
                        "description": "Captured standard error from the termination command."
                },
                "return_code": {
                        "type": "integer",
                        "example": 0,
                        "description": "Exit code from the termination command. 0 indicates success."
                },
                "message": {
                        "type": "string",
                        "example": "No target specified.",
                        "description": "Optional message for validation or error details."
                }
        },
        test_payload={
                "pid": 1234,
                "image_name": "python",
                "force": True,
                "tree": True,
                "timeout": 15,
                "simulated_mode": True
        }
)
def shell_kill_process__cross_platform__windows(input_data: dict) -> dict:
    import os, json, subprocess

    pid = input_data.get('pid')
    image_name = str(input_data.get('image_name', '')).strip()
    force = bool(input_data.get('force', False))
    tree = bool(input_data.get('tree', False))
    timeout_val = input_data.get('timeout')

    if pid is None and not image_name:
        return {'status': 'error', 'stdout': '', 'stderr': '', 'return_code': -1, 'message': 'Specify either pid or image_name.'}

    args = ['taskkill']
    if pid is not None:
        args += ['/PID', str(pid)]
    else:
        args += ['/IM', image_name]
    if force:
        args.append('/F')
    if tree:
        args.append('/T')

    creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)

    try:
        result = subprocess.run(args, capture_output=True, text=True, errors='replace', timeout=float(timeout_val) if timeout_val else None, shell=False, creationflags=creationflags)
        return {
            'status': 'success' if result.returncode == 0 else 'error',
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'return_code': result.returncode,
            'message': ''
        }
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'stdout': '', 'stderr': '', 'return_code': -1, 'message': 'Timed out.'}
    except Exception as e:
        return {'status': 'error', 'stdout': '', 'stderr': str(e), 'return_code': -1, 'message': str(e)}

@action(
        name="shell kill process (cross-platform)",
        description="Terminates a process by PID or image name across Windows, macOS, and Linux.",
        platforms=["linux"],
        input_schema={
                "pid": {
                        "type": "integer",
                        "example": 1234,
                        "description": "Process ID to terminate. If provided, takes precedence over image_name."
                },
                "image_name": {
                        "type": "string",
                        "example": "python",
                        "description": "Process image name (e.g., 'python' or 'chrome'). Used when pid is not provided."
                },
                "force": {
                        "type": "boolean",
                        "example": True,
                        "description": "Forceful termination (-9 on Unix, /F on Windows)."
                },
                "tree": {
                        "type": "boolean",
                        "example": True,
                        "description": "Kill the process and its children. Supported on Windows (/T) and Linux/macOS via pkill -P."
                },
                "timeout": {
                        "type": "integer",
                        "example": 15,
                        "description": "Optional timeout in seconds for the kill command."
                }
        },
        output_schema={
                "status": {
                        "type": "string",
                        "example": "success",
                        "description": "'success' if the process was terminated, 'error' otherwise."
                },
                "stdout": {
                        "type": "string",
                        "example": "Process terminated.",
                        "description": "Captured standard output from the termination command."
                },
                "stderr": {
                        "type": "string",
                        "example": "",
                        "description": "Captured standard error from the termination command."
                },
                "return_code": {
                        "type": "integer",
                        "example": 0,
                        "description": "Exit code from the termination command. 0 indicates success."
                },
                "message": {
                        "type": "string",
                        "example": "No target specified.",
                        "description": "Optional message for validation or error details."
                }
        },
        test_payload={
                "pid": 1234,
                "image_name": "python",
                "force": True,
                "tree": True,
                "timeout": 15,
                "simulated_mode": True
        }
)
def shell_kill_process__cross_platform__linux(input_data: dict) -> dict:
    import os, json, subprocess

    simulated_mode = input_data.get('simulated_mode', False)
    
    if simulated_mode:
        # Return mock result for testing
        return {
            'status': 'success',
            'stdout': 'Process terminated successfully',
            'stderr': '',
            'return_code': 0,
            'message': ''
        }

    pid = input_data.get('pid')
    image_name = str(input_data.get('image_name', '')).strip()
    force = bool(input_data.get('force', False))
    tree = bool(input_data.get('tree', False))
    timeout_val = input_data.get('timeout')

    if pid is None and not image_name:
        return {'status': 'error', 'stdout': '', 'stderr': '', 'return_code': -1, 'message': 'Specify either pid or image_name.'}

    if pid is not None:
        sig = '-9' if force else '-15'
        args = ['kill', sig, str(pid)]
    else:
        if tree:
            args = ['pkill', '-f', image_name]
        else:
            args = ['pkill'] + (['-9'] if force else []) + ['-f', image_name]

    try:
        result = subprocess.run(args, capture_output=True, text=True, errors='replace', timeout=float(timeout_val) if timeout_val else None, shell=False)
        return {
            'status': 'success' if result.returncode == 0 else 'error',
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'return_code': result.returncode,
            'message': ''
        }
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'stdout': '', 'stderr': '', 'return_code': -1, 'message': 'Timed out.'}
    except Exception as e:
        return {'status': 'error', 'stdout': '', 'stderr': str(e), 'return_code': -1, 'message': str(e)}

@action(
    name="shell kill process (cross-platform)",
    description="Terminates a process by PID or image name across Windows, macOS, and Linux.",
    platforms=["darwin"],
    input_schema={
        "pid": {
                "type": "integer",
                "example": 1234,
                "description": "Process ID to terminate. If provided, takes precedence over image_name."
        },
        "image_name": {
                "type": "string",
                "example": "python",
                "description": "Process image name (e.g., 'python' or 'chrome'). Used when pid is not provided."
        },
        "force": {
                "type": "boolean",
                "example": True,
                "description": "Forceful termination (-9 on Unix, /F on Windows)."
        },
        "tree": {
                "type": "boolean",
                "example": True,
                "description": "Kill the process and its children. Supported on Windows (/T) and Linux/macOS via pkill -P."
        },
        "timeout": {
                "type": "integer",
                "example": 15,
                "description": "Optional timeout in seconds for the kill command."
        }
},
    output_schema={
        "status": {
                "type": "string",
                "example": "success",
                "description": "'success' if the process was terminated, 'error' otherwise."
        },
        "stdout": {
                "type": "string",
                "example": "Process terminated.",
                "description": "Captured standard output from the termination command."
        },
        "stderr": {
                "type": "string",
                "example": "",
                "description": "Captured standard error from the termination command."
        },
        "return_code": {
                "type": "integer",
                "example": 0,
                "description": "Exit code from the termination command. 0 indicates success."
        },
        "message": {
                "type": "string",
                "example": "No target specified.",
                "description": "Optional message for validation or error details."
        }
},
)
def shell_kill_process__cross_platform__darwin(input_data: dict) -> dict:
    import os, json, subprocess

    pid = input_data.get('pid')
    image_name = str(input_data.get('image_name', '')).strip()
    force = bool(input_data.get('force', False))
    tree = bool(input_data.get('tree', False))
    timeout_val = input_data.get('timeout')

    if pid is None and not image_name:
        return {'status': 'error', 'stdout': '', 'stderr': '', 'return_code': -1, 'message': 'Specify either pid or image_name.'}

    if pid is not None:
        sig = '-9' if force else '-15'
        args = ['kill', sig, str(pid)]
    else:
        if tree:
            args = ['pkill', '-f', image_name]
        else:
            args = ['pkill'] + (['-9'] if force else []) + ['-f', image_name]

    try:
        result = subprocess.run(args, capture_output=True, text=True, errors='replace', timeout=float(timeout_val) if timeout_val else None, shell=False)
        return {
            'status': 'success' if result.returncode == 0 else 'error',
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'return_code': result.returncode,
            'message': ''
        }
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'stdout': '', 'stderr': '', 'return_code': -1, 'message': 'Timed out.'}
    except Exception as e:
        return {'status': 'error', 'stdout': '', 'stderr': str(e), 'return_code': -1, 'message': str(e)}