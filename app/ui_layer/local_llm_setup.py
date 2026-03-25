# -*- coding: utf-8 -*-
"""Local LLM setup utilities for Ollama."""

import asyncio
import json
import logging
import platform
import socket
import subprocess
import urllib.error
import urllib.request
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)

OLLAMA_DEFAULT_URL = "http://localhost:11434"


def check_port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if a TCP port is open."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def get_ollama_status() -> Dict[str, Any]:
    """Return Ollama installation and runtime status."""
    installed = False
    version = None

    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            installed = True
            version = result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    running = check_port_open("localhost", 11434)

    return {
        "installed": installed,
        "running": running,
        "version": version,
        "default_url": OLLAMA_DEFAULT_URL,
    }


def test_ollama_connection_sync(url: str) -> Dict[str, Any]:
    """Test an HTTP connection to an Ollama instance (synchronous)."""
    try:
        tags_url = url.rstrip("/") + "/api/tags"
        with urllib.request.urlopen(tags_url, timeout=5) as resp:
            data = json.loads(resp.read())
        models = [m["name"] for m in data.get("models", [])]
        if models:
            msg = f"Connected! {len(models)} model(s) available."
        else:
            msg = "Connected! No models downloaded yet — run 'ollama pull llama3' to get one."
        return {"success": True, "models": models, "message": msg}
    except urllib.error.URLError as exc:
        return {"success": False, "error": f"Cannot connect: {exc.reason}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


async def install_ollama(progress_callback: Callable) -> Dict[str, Any]:
    """Install Ollama for the current platform, streaming progress via callback."""
    system = platform.system()

    try:
        if system == "Windows":
            # Try winget first
            await progress_callback("Checking for winget...")
            try:
                proc = await asyncio.create_subprocess_exec(
                    "winget", "install", "--id", "Ollama.Ollama",
                    "--accept-package-agreements", "--accept-source-agreements",
                    "--silent",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await progress_callback("Installing Ollama via winget (this may take a minute)...")
                _, stderr = await proc.communicate()
                if proc.returncode == 0:
                    await progress_callback("Ollama installed successfully!")
                    return {"success": True, "message": "Ollama installed via winget"}
                await progress_callback("winget install failed, switching to direct download...")
            except FileNotFoundError:
                await progress_callback("winget not found — downloading installer directly...")

            # Direct download fallback
            import os
            tmp = os.environ.get("TEMP", os.getcwd())
            installer_path = os.path.join(tmp, "OllamaSetup.exe")
            installer_url = "https://ollama.com/download/OllamaSetup.exe"

            await progress_callback("Downloading Ollama installer from ollama.com...")
            dl_proc = await asyncio.create_subprocess_exec(
                "powershell", "-Command",
                f"Invoke-WebRequest -Uri '{installer_url}' -OutFile '{installer_path}' -UseBasicParsing",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await dl_proc.communicate()
            if dl_proc.returncode != 0:
                err = stderr.decode(errors="replace")[:300]
                return {"success": False, "error": f"Download failed: {err}"}

            await progress_callback("Running installer silently...")
            run_proc = await asyncio.create_subprocess_exec(
                installer_path, "/S",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await run_proc.communicate()
            await progress_callback("Installation complete!")
            return {"success": True, "message": "Ollama installed"}

        elif system in ("Darwin", "Linux"):
            await progress_callback("Downloading Ollama install script...")
            proc = await asyncio.create_subprocess_exec(
                "sh", "-c", "curl -fsSL https://ollama.com/install.sh | sh",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            # Stream stdout lines as progress
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                text = line.decode(errors="replace").strip()
                if text:
                    await progress_callback(text[:120])

            await proc.wait()
            if proc.returncode == 0:
                await progress_callback("Ollama installed successfully!")
                return {"success": True}
            else:
                return {"success": False, "error": "Install script exited with an error"}

        else:
            return {"success": False, "error": f"Unsupported platform: {system}"}

    except Exception as exc:
        logger.exception("Error installing Ollama")
        return {"success": False, "error": str(exc)}


async def start_ollama() -> Dict[str, Any]:
    """Start the Ollama server in the background and wait for it to become ready."""
    try:
        kwargs: Dict[str, Any] = {
            "stdout": asyncio.subprocess.DEVNULL,
            "stderr": asyncio.subprocess.DEVNULL,
        }
        if platform.system() == "Windows":
            kwargs["creationflags"] = 0x00000008  # DETACHED_PROCESS

        await asyncio.create_subprocess_exec("ollama", "serve", **kwargs)

        # Poll until ready (max 15 seconds)
        for _ in range(15):
            await asyncio.sleep(1)
            if check_port_open("localhost", 11434):
                return {"success": True, "message": "Ollama started successfully"}

        return {"success": False, "error": "Ollama started but not responding on port 11434"}

    except FileNotFoundError:
        return {"success": False, "error": "Ollama executable not found — is it installed?"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
