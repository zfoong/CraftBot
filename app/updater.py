"""CraftBot updater — version checking, update, and restart logic.

This module is the single source of truth for all update operations.
Both the /update command and browser adapter handlers call into this module.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Awaitable, Callable, Optional, Tuple


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------

def parse_version(version_str: str) -> Tuple[int, ...]:
    """Parse 'X.Y.Z' into an (X, Y, Z) integer tuple."""
    parts = version_str.strip().lstrip("vV").split(".")
    return tuple(int(p) for p in parts)


def is_newer(remote: str, local: str) -> bool:
    """Return True if *remote* version is strictly newer than *local*."""
    try:
        return parse_version(remote) > parse_version(local)
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# Remote version check
# ---------------------------------------------------------------------------

GITHUB_REPO = "CraftOS-dev/CraftBot"
GITHUB_LATEST_RELEASE_URL = (
    f"https://api.github.com/repos/{GITHUB_REPO}/tags"
)


async def check_for_update() -> Tuple[bool, str, str]:
    """Check whether a newer version is available on the remote repo.

    Fetches the latest git tag from GitHub (e.g. ``v1.2.2``) and compares
    it against the local version stored in settings.json.

    Returns:
        (update_available, current_version, latest_version)
    """
    from app.config import get_app_version

    import aiohttp

    current = get_app_version()
    try:
        headers = {"Accept": "application/vnd.github.v3+json"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                GITHUB_LATEST_RELEASE_URL,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                tags = await resp.json(content_type=None)

        if not tags or not isinstance(tags, list):
            return False, current, current

        # Find the highest semver tag (tags are not guaranteed sorted)
        latest = "0.0.0"
        for tag in tags:
            name = tag.get("name", "")
            try:
                if parse_version(name) > parse_version(latest):
                    latest = name.strip().lstrip("vV")
            except (ValueError, AttributeError):
                continue

    except Exception:
        # Network error — treat as "no update available"
        return False, current, current

    return is_newer(latest, current), current, latest


# ---------------------------------------------------------------------------
# Perform update
# ---------------------------------------------------------------------------

RESTART_EXIT_CODE = 42


async def perform_update(
    progress_callback: Optional[Callable[[str], Awaitable[None]]] = None,
) -> None:
    """Pull the latest code from GitHub, run install, and trigger a restart.

    Args:
        progress_callback: An async callable invoked with human-readable
            progress messages.  Each interface (browser, TUI, CLI) supplies
            its own implementation so the user sees live feedback.
    """

    async def emit(msg: str) -> None:
        if progress_callback:
            await progress_callback(msg)

    project_root = str(Path(__file__).resolve().parent.parent)

    # 1. Stash local changes if the working tree is dirty
    proc = await asyncio.create_subprocess_exec(
        "git", "status", "--porcelain",
        cwd=project_root,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    if stdout.strip():
        await emit("Stashing local changes...")
        await _run_git(["git", "stash"], project_root)

    # 2. Fetch and pull latest from main
    await emit("Fetching latest version...")
    await _run_git(["git", "fetch", "origin", "main"], project_root)

    await emit("Pulling latest code...")
    await _run_git(["git", "checkout", "main"], project_root)
    await _run_git(["git", "pull", "origin", "main"], project_root)

    # 3. Re-run install.py for dependency updates
    await emit("Installing dependencies...")
    install_script = os.path.join(project_root, "install.py")
    if os.path.exists(install_script):
        proc = await asyncio.create_subprocess_exec(
            sys.executable, install_script,
            cwd=project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

    # 4. Signal restart
    await emit("Update complete! Restarting CraftBot...")
    await asyncio.sleep(1)  # allow the message to reach the UI

    # Force-exit with a special code so run.py can re-launch everything
    os._exit(RESTART_EXIT_CODE)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _run_git(cmd: list, cwd: str) -> Tuple[bytes, bytes]:
    """Run a git command asynchronously and return (stdout, stderr)."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    return await proc.communicate()
