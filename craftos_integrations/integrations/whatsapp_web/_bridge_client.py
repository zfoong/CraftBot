# -*- coding: utf-8 -*-
"""Python client for the WhatsApp Node.js bridge process.

Manages the Node.js subprocess lifecycle and provides an async API for
sending commands and receiving events via stdin/stdout JSON lines.
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, Optional

from ...config import ConfigStore
from ...logger import get_logger

logger = get_logger(__name__)

BRIDGE_DIR = Path(__file__).parent
BRIDGE_SCRIPT = BRIDGE_DIR / "bridge.js"

EventCallback = Callable[[str, Dict[str, Any]], Coroutine[Any, Any, None]]


class WhatsAppBridge:
    def __init__(self, auth_dir: Optional[str] = None):
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._pending: Dict[str, asyncio.Future] = {}
        self._event_callback: Optional[EventCallback] = None
        self._running = False
        self._ready = False
        self._owner_phone = ""
        self._owner_name = ""
        self._wid = ""

        if auth_dir:
            self._auth_dir = auth_dir
        else:
            self._auth_dir = str(ConfigStore.project_root / ".credentials" / "whatsapp_wwebjs_auth")

    @property
    def is_running(self) -> bool:
        return self._running and self._process is not None and self._process.returncode is None

    @property
    def is_ready(self) -> bool:
        return self._ready and self.is_running

    @property
    def owner_phone(self) -> str:
        return self._owner_phone

    @property
    def owner_name(self) -> str:
        return self._owner_name

    def set_event_callback(self, callback: Optional[EventCallback]) -> None:
        self._event_callback = callback

    async def start(self) -> None:
        if self.is_running:
            return

        auth_dir = Path(self._auth_dir)
        if os.name == "nt":
            try:
                result = subprocess.run(
                    ["wmic", "process", "where",
                     f"commandline like '%{auth_dir.name}%' and name='chrome.exe'",
                     "get", "processid"],
                    capture_output=True, text=True, timeout=5,
                )
                for line in result.stdout.strip().split("\n")[1:]:
                    pid = line.strip()
                    if pid.isdigit():
                        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=5)
            except Exception:
                pass
        lock_file = auth_dir / "session" / "SingletonLock"
        if lock_file.exists():
            try:
                lock_file.unlink(missing_ok=True)
            except Exception:
                pass

        node_modules = BRIDGE_DIR / "node_modules"
        if not node_modules.exists():
            logger.info("[WA-Bridge] Installing npm dependencies...")
            npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
            proc = await asyncio.create_subprocess_exec(
                npm_cmd, "install",
                cwd=str(BRIDGE_DIR),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            if proc.returncode != 0:
                stderr = await proc.stderr.read()
                raise RuntimeError(f"npm install failed: {stderr.decode()}")

        logger.info(f"[WA-Bridge] Starting bridge (auth_dir={self._auth_dir})")

        node_cmd = "node.exe" if os.name == "nt" else "node"
        self._process = await asyncio.create_subprocess_exec(
            node_cmd, str(BRIDGE_SCRIPT), self._auth_dir,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._running = True
        self._reader_task = asyncio.create_task(self._read_stdout())
        self._stderr_task = asyncio.create_task(self._read_stderr())

    async def stop(self) -> None:
        if not self.is_running:
            return
        self._running = False
        self._ready = False

        try:
            await self.send_command("shutdown", timeout=10.0)
        except Exception:
            pass

        if self._process:
            try:
                await asyncio.wait_for(self._process.wait(), timeout=20.0)
            except asyncio.TimeoutError:
                if os.name == "nt":
                    try:
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(self._process.pid)],
                            capture_output=True, timeout=5,
                        )
                    except Exception:
                        self._process.kill()
                else:
                    self._process.kill()

        for task in [self._reader_task, self._stderr_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._process = None
        self._reader_task = None
        self._stderr_task = None

        for req_id, future in self._pending.items():
            if not future.done():
                future.set_exception(RuntimeError("Bridge stopped"))
        self._pending.clear()

    async def send_command(self, cmd: str, args: Optional[Dict[str, Any]] = None,
                           timeout: float = 30.0) -> Dict[str, Any]:
        if not self.is_running:
            raise RuntimeError("Bridge not running")

        req_id = f"req_{uuid.uuid4().hex[:8]}"
        payload = json.dumps({"id": req_id, "cmd": cmd, "args": args or {}})

        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[req_id] = future

        try:
            self._process.stdin.write((payload + "\n").encode())
            await self._process.stdin.drain()
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            raise TimeoutError(f"Command '{cmd}' timed out after {timeout}s")
        except Exception:
            self._pending.pop(req_id, None)
            raise

    async def send_message(self, to: str, text: str) -> Dict[str, Any]:
        return await self.send_command("send_message", {"to": to, "text": text})

    async def get_status(self) -> Dict[str, Any]:
        return await self.send_command("get_status")

    async def get_chats(self, limit: int = 50) -> Dict[str, Any]:
        return await self.send_command("get_chats", {"limit": limit})

    async def get_chat_messages(self, chat_id: str, limit: int = 50) -> Dict[str, Any]:
        return await self.send_command("get_chat_messages", {"chat_id": chat_id, "limit": limit})

    async def search_contact(self, name: str) -> Dict[str, Any]:
        return await self.send_command("search_contact", {"name": name})

    async def get_unread_chats(self) -> Dict[str, Any]:
        return await self.send_command("get_unread_chats")

    async def wait_for_ready(self, timeout: float = 120.0) -> bool:
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            if self._ready:
                return True
            if not self.is_running:
                return False
            await asyncio.sleep(0.5)
        return False

    async def wait_for_qr_or_ready(self, timeout: float = 120.0):
        if self._ready:
            return "ready", {
                "owner_phone": self._owner_phone,
                "owner_name": self._owner_name,
                "wid": self._wid,
            }

        event_received = asyncio.Event()
        result = {"type": None, "data": None}
        original_callback = self._event_callback

        async def intercept_callback(event: str, data: dict):
            if event in ("qr", "ready") and result["type"] is None:
                result["type"] = event
                result["data"] = data
                event_received.set()
            if original_callback:
                await original_callback(event, data)

        self._event_callback = intercept_callback
        try:
            await asyncio.wait_for(event_received.wait(), timeout=timeout)
            return result["type"], result["data"]
        except asyncio.TimeoutError:
            return "timeout", None
        finally:
            self._event_callback = original_callback

    async def _read_stdout(self) -> None:
        try:
            while self._running and self._process and self._process.stdout:
                line = await self._process.stdout.readline()
                if not line:
                    break
                try:
                    data = json.loads(line.decode().strip())
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type")
                if msg_type == "response":
                    req_id = data.get("id")
                    future = self._pending.pop(req_id, None)
                    if future and not future.done():
                        future.set_result(data.get("data", {}))
                elif msg_type == "event":
                    event = data.get("event", "")
                    event_data = data.get("data", {})
                    self._handle_event(event, event_data)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[WA-Bridge] stdout reader error: {e}")
        finally:
            if self._running:
                self._ready = False

    async def _read_stderr(self) -> None:
        try:
            while self._running and self._process and self._process.stderr:
                line = await self._process.stderr.readline()
                if not line:
                    break
                text = line.decode().strip()
                if text:
                    logger.info(f"[WA-Bridge:node] {text}")
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    def _handle_event(self, event: str, data: Dict[str, Any]) -> None:
        if event == "ready":
            self._ready = True
            self._owner_phone = data.get("owner_phone", "")
            self._owner_name = data.get("owner_name", "")
            self._wid = data.get("wid", "")
        elif event == "disconnected":
            self._ready = False

        if self._event_callback:
            asyncio.ensure_future(self._event_callback(event, data))


_bridge_instance: Optional[WhatsAppBridge] = None


def get_whatsapp_bridge() -> WhatsAppBridge:
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = WhatsAppBridge()
    return _bridge_instance
