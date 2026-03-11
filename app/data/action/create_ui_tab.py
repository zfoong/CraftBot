from agent_core import action

@action(
    name="create_ui_tab",
    description="Create a new dynamic tab in the browser UI. Use this to display structured data in a dedicated tab. "
                "For 'code' tabs: just pass a folder path — the tab will automatically show git diff (or list files if not a git repo). "
                "For other types: 'stock' (ticker data, price charts), 'planner' (milestones, kanban tasks), 'custom' (free-form markdown). "
                "The tab will be linked to the current task.",
    default=False,
    action_sets=["browser_ui"],
    parallelizable=False,
    input_schema={
        "tab_type": {
            "type": "string",
            "enum": ["code", "stock", "planner", "custom"],
            "description": "The type of tab to create."
        },
        "label": {
            "type": "string",
            "example": "Code Changes",
            "description": "Display label for the tab in the navigation bar."
        },
        "initial_data": {
            "type": "object",
            "description": (
                "Optional initial data. Structure depends on tab_type:\n"
                "- code: {\"path\": \"/path/to/repo\"} — the tab runs git diff automatically.\n"
                "- stock: {\"ticker\": \"AAPL\", \"summary\": \"...\"}\n"
                "- planner: {\"summary\": \"...\", \"tasks\": [...]}\n"
                "- custom: {\"content\": \"markdown text\", \"title\": \"...\"}"
            ),
            "example": {"path": "/home/user/project"}
        }
    },
    output_schema={
        "status": {
            "type": "string",
            "example": "ok",
            "description": "'ok' if tab was created, 'error' if creation failed."
        },
        "tab_type": {
            "type": "string",
            "description": "The type of tab that was created."
        },
        "task_id": {
            "type": "string",
            "description": "The task ID the tab is linked to."
        },
        "error": {
            "type": "string",
            "description": "Error message if status is 'error'."
        }
    },
    test_payload={
        "tab_type": "custom",
        "label": "Test Tab",
        "initial_data": {"content": "# Hello\nThis is a test tab."},
        "simulated_mode": True
    }
)
def create_ui_tab(input_data: dict) -> dict:
    import asyncio

    tab_type = input_data.get("tab_type", "custom")
    label = input_data.get("label", "")
    initial_data = input_data.get("initial_data")
    simulated_mode = input_data.get("simulated_mode", False)

    # Validate tab_type
    valid_types = ("code", "stock", "planner", "custom")
    if tab_type not in valid_types:
        return {"status": "error", "error": f"Invalid tab_type '{tab_type}'. Must be one of: {valid_types}"}

    if simulated_mode:
        return {"status": "ok", "tab_type": tab_type, "task_id": "sim-task-001", "label": label}

    # For code tabs, resolve path to git diff
    if tab_type == "code" and initial_data and initial_data.get("path"):
        initial_data = _resolve_code_data(initial_data["path"])

    # Get the current task ID
    import app.internal_action_interface as iai
    task_id = iai.InternalActionInterface._get_current_task_id()
    if not task_id:
        return {"status": "error", "error": "No active task. Cannot create a tab without an active task context."}

    result = asyncio.run(iai.InternalActionInterface.create_dynamic_tab(
        tab_type=tab_type,
        task_id=task_id,
        label=label,
        initial_data=initial_data,
    ))

    return result


def _resolve_code_data(path: str) -> dict:
    """Run git diff at the given path. Falls back to file listing if not a git repo."""
    import subprocess
    import os

    if not os.path.isdir(path):
        return {"summary": f"Path not found: {path}"}

    # Check if it's a git repo
    is_git = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path, capture_output=True, text=True, timeout=10,
    ).returncode == 0

    if is_git:
        raw_diff = _get_git_diff(path)

        if not raw_diff:
            return {"summary": "No changes detected in this repository."}

        return {"rawDiff": raw_diff}
    else:
        # Not a git repo — list files
        files = []
        for root, _dirs, filenames in os.walk(path):
            for f in filenames:
                rel = os.path.relpath(os.path.join(root, f), path)
                files.append(rel)
                if len(files) >= 200:
                    break
            if len(files) >= 200:
                break

        file_list = "\n".join(f"- {f}" for f in sorted(files))
        summary = f"**{len(files)} files** in `{path}`" + (" (truncated to 200)" if len(files) >= 200 else "")
        return {"summary": f"{summary}\n\n{file_list}"}


def _get_git_diff(path: str) -> str:
    """Get uncommitted changes (staged + unstaged + untracked), like VS Code source control."""
    import subprocess
    import os

    def _run(cmd: list) -> str:
        r = subprocess.run(cmd, cwd=path, capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else ""

    # Staged + unstaged combined
    raw_diff = _run(["git", "diff", "HEAD"])
    if not raw_diff:
        # Fallback: unstaged only (covers repos with no commits yet)
        raw_diff = _run(["git", "diff"])

    # Also include untracked files (like VS Code shows new files)
    untracked = _run(["git", "ls-files", "--others", "--exclude-standard"])
    if untracked:
        untracked_diff_parts = []
        for rel_path in untracked.splitlines():
            full = os.path.join(path, rel_path)
            # Skip binary / very large files
            try:
                size = os.path.getsize(full)
                if size > 100_000:
                    untracked_diff_parts.append(
                        f"diff --git a/{rel_path} b/{rel_path}\n"
                        f"new file mode 100644\n"
                        f"--- /dev/null\n"
                        f"+++ b/{rel_path}\n"
                        f"@@ -0,0 +1 @@\n"
                        f"+Binary or large file ({size} bytes)"
                    )
                    continue
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except (OSError, UnicodeDecodeError):
                continue

            if not lines:
                continue

            added = "".join(f"+{line}" if line.endswith("\n") else f"+{line}\n" for line in lines)
            untracked_diff_parts.append(
                f"diff --git a/{rel_path} b/{rel_path}\n"
                f"new file mode 100644\n"
                f"--- /dev/null\n"
                f"+++ b/{rel_path}\n"
                f"@@ -0,0 +1,{len(lines)} @@\n"
                f"{added.rstrip()}"
            )

        if untracked_diff_parts:
            untracked_diff = "\n".join(untracked_diff_parts)
            raw_diff = f"{raw_diff}\n{untracked_diff}" if raw_diff else untracked_diff

    return raw_diff
