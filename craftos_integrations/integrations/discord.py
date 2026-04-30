# -*- coding: utf-8 -*-
"""Discord integration — bot + user account + voice (lazy)."""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote as _url_quote

import httpx

from .. import (
    BasePlatformClient,
    IntegrationHandler,
    IntegrationSpec,
    PlatformMessage,
    has_credential,
    load_credential,
    register_client,
    register_handler,
    remove_credential,
    save_credential,
)
from ..helpers import Result, request as http_request
from ..logger import get_logger

logger = get_logger(__name__)

DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_GATEWAY_URL = "wss://gateway.discord.gg/?v=10&encoding=json"
GATEWAY_INTENTS = (1 << 9) | (1 << 12) | (1 << 15)  # 37376


@dataclass
class DiscordCredential:
    bot_token: str = ""
    user_token: str = ""


DISCORD = IntegrationSpec(
    name="discord",
    cred_class=DiscordCredential,
    cred_file="discord.json",
    platform_id="discord",
)


# ════════════════════════════════════════════════════════════════════════
# Handler
# ════════════════════════════════════════════════════════════════════════

@register_handler(DISCORD.name)
class DiscordHandler(IntegrationHandler):
    spec = DISCORD
    display_name = "Discord"
    description = "Community chat"
    auth_type = "token"
    fields = [
        {"key": "bot_token", "label": "Bot Token", "placeholder": "Enter bot token", "password": True},
    ]

    @property
    def subcommands(self) -> List[str]:
        return ["login", "logout", "status"]

    async def login(self, args: List[str]) -> Tuple[bool, str]:
        if not args:
            return False, "Usage: /discord login <bot_token>"
        bot_token = args[0]
        try:
            r = httpx.get(
                "https://discord.com/api/v10/users/@me",
                headers={"Authorization": f"Bot {bot_token}"},
                timeout=15,
            )
            if r.status_code != 200:
                return False, f"Invalid bot token: {r.status_code}"
            data = r.json()
        except Exception as e:
            return False, f"Discord connection error: {e}"

        save_credential(self.spec.cred_file, DiscordCredential(bot_token=bot_token))
        return True, f"Discord bot connected: {data.get('username')} ({data.get('id')})"

    async def logout(self, args: List[str]) -> Tuple[bool, str]:
        if not has_credential(self.spec.cred_file):
            return False, "No Discord credentials found."
        try:
            from ..manager import get_external_comms_manager
            manager = get_external_comms_manager()
            if manager:
                await manager.stop_platform(self.spec.platform_id)
        except Exception:
            pass
        remove_credential(self.spec.cred_file)
        return True, "Removed Discord credential."

    async def status(self) -> Tuple[bool, str]:
        if not has_credential(self.spec.cred_file):
            return True, "Discord: Not connected"
        cred = load_credential(self.spec.cred_file, DiscordCredential)
        if not cred or not cred.bot_token:
            return True, "Discord: Not connected"
        return True, "Discord: Connected (bot token)"


# ════════════════════════════════════════════════════════════════════════
# Client
# ════════════════════════════════════════════════════════════════════════

@register_client
class DiscordClient(BasePlatformClient):
    """Unified Discord client exposing bot, user, and voice operations."""
    spec = DISCORD
    PLATFORM_ID = DISCORD.platform_id

    def __init__(self) -> None:
        super().__init__()
        self._cred: Optional[DiscordCredential] = None
        self._ws = None
        self._ws_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval: float = 41.25
        self._last_sequence: Optional[int] = None
        self._bot_user_id: Optional[str] = None
        self._catchup_done: bool = False
        # Lazy voice manager — created/started on first voice call, reused after
        self._voice_mgr: Optional[Any] = None

    def has_credentials(self) -> bool:
        return has_credential(self.spec.cred_file)

    def _load(self) -> DiscordCredential:
        if self._cred is None:
            self._cred = load_credential(self.spec.cred_file, DiscordCredential)
        if self._cred is None:
            raise RuntimeError("No Discord credentials. Use /discord login first.")
        return self._cred

    def _bot_token(self) -> str:
        cred = self._load()
        if not cred.bot_token:
            raise RuntimeError("No Discord bot_token configured.")
        return cred.bot_token

    def _user_token(self) -> str:
        cred = self._load()
        if not cred.user_token:
            raise RuntimeError("No Discord user_token configured.")
        return cred.user_token

    def _bot_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bot {self._bot_token()}", "Content-Type": "application/json"}

    def _user_headers(self) -> Dict[str, str]:
        return {"Authorization": self._user_token(), "Content-Type": "application/json"}

    async def connect(self) -> None:
        self._load()
        self._connected = True

    @property
    def supports_listening(self) -> bool:
        return True

    async def start_listening(self, callback) -> None:
        if self._listening:
            return
        self._message_callback = callback
        cred = self._load()
        if not cred.bot_token:
            raise RuntimeError("No Discord bot token for Gateway connection")

        bot_info = self.get_bot_user()
        if "error" in bot_info:
            raise RuntimeError(f"Invalid Discord bot token: {bot_info.get('error')}")
        self._bot_user_id = bot_info["result"]["id"]

        self._listening = True
        self._catchup_done = False
        self._ws_task = asyncio.create_task(self._gateway_loop())

    async def stop_listening(self) -> None:
        if not self._listening:
            return
        self._listening = False
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        self._heartbeat_task = None
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        self._ws_task = None

    async def _gateway_loop(self) -> None:
        import aiohttp
        while self._listening:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(DISCORD_GATEWAY_URL) as ws:
                        self._ws = ws
                        await self._handle_gateway(ws)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[DISCORD] Gateway error: {e}")
                if self._listening:
                    await asyncio.sleep(5)

    async def _handle_gateway(self, ws) -> None:
        import aiohttp as _aiohttp
        async for msg in ws:
            if not self._listening:
                break
            if msg.type == _aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    await self._process_gateway_event(ws, data)
                except Exception as e:
                    logger.error(f"[DISCORD] Error processing Gateway event: {e}")
            elif msg.type in (_aiohttp.WSMsgType.ERROR, _aiohttp.WSMsgType.CLOSED):
                break

    async def _process_gateway_event(self, ws, data: dict) -> None:
        op = data.get("op")
        t = data.get("t")
        d = data.get("d")
        s = data.get("s")
        if s is not None:
            self._last_sequence = s

        if op == 10:
            self._heartbeat_interval = d["heartbeat_interval"] / 1000.0
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop(ws))
            await ws.send_json({
                "op": 2,
                "d": {
                    "token": self._bot_token(),
                    "intents": GATEWAY_INTENTS,
                    "properties": {"os": "windows", "browser": "craftosbot", "device": "craftosbot"},
                },
            })
        elif op == 0:
            if t == "READY":
                asyncio.get_running_loop().call_later(2.0, self._mark_catchup_done)
            elif t == "MESSAGE_CREATE" and d:
                await self._handle_message_create(d)
        elif op == 1:
            await ws.send_json({"op": 1, "d": self._last_sequence})
        elif op in (7, 9):
            # 7 = reconnect requested, 9 = invalid session — both close the socket
            await ws.close()

    def _mark_catchup_done(self) -> None:
        self._catchup_done = True

    async def _heartbeat_loop(self, ws) -> None:
        try:
            while self._listening:
                await ws.send_json({"op": 1, "d": self._last_sequence})
                await asyncio.sleep(self._heartbeat_interval)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def _handle_message_create(self, d: dict) -> None:
        author = d.get("author", {})
        if author.get("id") == self._bot_user_id or author.get("bot"):
            return
        content = d.get("content", "")
        if not content or not self._catchup_done:
            return

        author_name = author.get("username", "Unknown")
        channel_id = d.get("channel_id", "")
        guild_id = d.get("guild_id", "")
        channel_name = f"#{channel_id}" if guild_id else "DM"

        ts = None
        try:
            ts = datetime.fromisoformat(d.get("timestamp", ""))
        except Exception:
            pass

        if self._message_callback:
            await self._message_callback(PlatformMessage(
                platform=self.spec.platform_id,
                sender_id=author.get("id", ""),
                sender_name=author_name,
                text=content,
                channel_id=channel_id,
                channel_name=channel_name,
                message_id=d.get("id", ""),
                timestamp=ts,
                raw={"guild_id": guild_id, "is_self_message": False},
            ))

    async def send_message(self, recipient: str, text: str, **kwargs) -> Result:
        return self.bot_send_message(channel_id=recipient, content=text, **kwargs)

    # ----- Bot REST API -----
    def get_bot_user(self) -> Result:
        return http_request(
            "GET", f"{DISCORD_API_BASE}/users/@me",
            headers=self._bot_headers(),
            transform=lambda d: {
                "id": d.get("id"), "username": d.get("username"),
                "discriminator": d.get("discriminator"), "avatar": d.get("avatar"),
                "bot": d.get("bot", True),
            },
        )

    def get_bot_guilds(self, limit: int = 100) -> Result:
        return http_request(
            "GET", f"{DISCORD_API_BASE}/users/@me/guilds",
            headers=self._bot_headers(), params={"limit": limit},
            transform=lambda d: {"guilds": d},
        )

    def get_guild_channels(self, guild_id: str) -> Result:
        return http_request(
            "GET", f"{DISCORD_API_BASE}/guilds/{guild_id}/channels",
            headers=self._bot_headers(),
            transform=lambda channels: {
                "all_channels": channels,
                "text_channels": [c for c in channels if c.get("type") == 0],
                "voice_channels": [c for c in channels if c.get("type") == 2],
                "categories": [c for c in channels if c.get("type") == 4],
            },
        )

    def get_channel(self, channel_id: str) -> Result:
        return http_request(
            "GET", f"{DISCORD_API_BASE}/channels/{channel_id}",
            headers=self._bot_headers(),
        )

    def bot_send_message(self, channel_id: str, content: str,
                         embed: Optional[Dict[str, Any]] = None,
                         reply_to: Optional[str] = None) -> Result:
        payload: Dict[str, Any] = {"content": content}
        if embed:
            payload["embeds"] = [embed]
        if reply_to:
            payload["message_reference"] = {"message_id": reply_to}
        return http_request(
            "POST", f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
            headers=self._bot_headers(), json=payload,
            transform=lambda d: {
                "message_id": d.get("id"), "channel_id": d.get("channel_id"),
                "content": d.get("content"), "timestamp": d.get("timestamp"),
            },
        )

    def get_messages(self, channel_id: str, limit: int = 50,
                     before: Optional[str] = None, after: Optional[str] = None) -> Result:
        params: Dict[str, Any] = {"limit": min(limit, 100)}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        return http_request(
            "GET", f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
            headers=self._bot_headers(), params=params, expected=(200,),
            transform=lambda messages: {
                "messages": [
                    {"id": m.get("id"), "content": m.get("content"),
                     "author": {"id": m.get("author", {}).get("id"),
                                "username": m.get("author", {}).get("username"),
                                "bot": m.get("author", {}).get("bot", False)},
                     "timestamp": m.get("timestamp"),
                     "attachments": m.get("attachments", []),
                     "embeds": m.get("embeds", [])}
                    for m in messages
                ],
                "count": len(messages),
            },
        )

    def edit_message(self, channel_id: str, message_id: str, content: str) -> Result:
        return http_request(
            "PATCH", f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}",
            headers=self._bot_headers(), json={"content": content}, expected=(200,),
        )

    def delete_message(self, channel_id: str, message_id: str) -> Result:
        return http_request(
            "DELETE", f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}",
            headers=self._bot_headers(), expected=(204,),
            transform=lambda _: {"deleted": True},
        )

    def create_dm_channel(self, recipient_id: str) -> Result:
        return http_request(
            "POST", f"{DISCORD_API_BASE}/users/@me/channels",
            headers=self._bot_headers(), json={"recipient_id": recipient_id},
            transform=lambda d: {
                "channel_id": d.get("id"), "type": d.get("type"),
                "recipients": d.get("recipients", []),
            },
        )

    def send_dm(self, recipient_id: str, content: str,
                embed: Optional[Dict[str, Any]] = None) -> Result:
        dm_result = self.create_dm_channel(recipient_id)
        if "error" in dm_result:
            return dm_result
        return self.bot_send_message(dm_result["result"]["channel_id"], content, embed)

    def get_user(self, user_id: str) -> Result:
        return http_request(
            "GET", f"{DISCORD_API_BASE}/users/{user_id}",
            headers=self._bot_headers(), expected=(200,),
        )

    def get_guild_member(self, guild_id: str, user_id: str) -> Result:
        return http_request(
            "GET", f"{DISCORD_API_BASE}/guilds/{guild_id}/members/{user_id}",
            headers=self._bot_headers(), expected=(200,),
        )

    def list_guild_members(self, guild_id: str, limit: int = 100) -> Result:
        return http_request(
            "GET", f"{DISCORD_API_BASE}/guilds/{guild_id}/members",
            headers=self._bot_headers(), params={"limit": min(limit, 1000)}, expected=(200,),
            transform=lambda members: {"members": members},
        )

    def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> Result:
        encoded_emoji = _url_quote(emoji, safe="")
        return http_request(
            "PUT",
            f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}/reactions/{encoded_emoji}/@me",
            headers=self._bot_headers(), expected=(204,),
            transform=lambda _: {"added": True, "emoji": emoji},
        )

    # ----- User-account methods -----
    def user_get_current_user(self) -> Result:
        return http_request(
            "GET", f"{DISCORD_API_BASE}/users/@me",
            headers=self._user_headers(), expected=(200,),
            transform=lambda d: {
                "id": d.get("id"), "username": d.get("username"),
                "discriminator": d.get("discriminator"), "email": d.get("email"),
                "avatar": d.get("avatar"),
            },
        )

    def user_get_guilds(self, limit: int = 100) -> Result:
        return http_request(
            "GET", f"{DISCORD_API_BASE}/users/@me/guilds",
            headers=self._user_headers(), params={"limit": limit}, expected=(200,),
            transform=lambda d: {"guilds": d},
        )

    def user_get_dm_channels(self) -> Result:
        return http_request(
            "GET", f"{DISCORD_API_BASE}/users/@me/channels",
            headers=self._user_headers(), expected=(200,),
            transform=lambda channels: {
                "dm_channels": [
                    {"id": c.get("id"), "type": c.get("type"),
                     "recipients": [{"id": rec.get("id"), "username": rec.get("username")}
                                    for rec in c.get("recipients", [])],
                     "last_message_id": c.get("last_message_id")}
                    for c in channels
                ],
                "count": len(channels),
            },
        )

    def user_send_message(self, channel_id: str, content: str,
                          reply_to: Optional[str] = None) -> Result:
        payload: Dict[str, Any] = {"content": content}
        if reply_to:
            payload["message_reference"] = {"message_id": reply_to}
        return http_request(
            "POST", f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
            headers=self._user_headers(), json=payload,
            transform=lambda d: {
                "message_id": d.get("id"), "channel_id": d.get("channel_id"),
                "content": d.get("content"), "timestamp": d.get("timestamp"),
            },
        )

    def user_get_messages(self, channel_id: str, limit: int = 50,
                          before: Optional[str] = None, after: Optional[str] = None) -> Result:
        params: Dict[str, Any] = {"limit": min(limit, 100)}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        return http_request(
            "GET", f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
            headers=self._user_headers(), params=params, expected=(200,),
            transform=lambda messages: {
                "messages": [
                    {"id": m.get("id"), "content": m.get("content"),
                     "author": {"id": m.get("author", {}).get("id"),
                                "username": m.get("author", {}).get("username")},
                     "timestamp": m.get("timestamp"),
                     "attachments": m.get("attachments", [])}
                    for m in messages
                ],
                "count": len(messages),
            },
        )

    def user_send_dm(self, recipient_id: str, content: str) -> Result:
        result = http_request(
            "POST", f"{DISCORD_API_BASE}/users/@me/channels",
            headers=self._user_headers(), json={"recipient_id": recipient_id},
        )
        if "error" in result:
            return result
        channel_id = result.get("result", {}).get("id")
        return self.user_send_message(channel_id, content)

    def user_get_relationships(self) -> Result:
        def _shape(relationships):
            friends = [r for r in relationships if r.get("type") == 1]
            return {
                "friends": [{"id": r.get("id"),
                             "username": r.get("user", {}).get("username")} for r in friends],
                "blocked": [r for r in relationships if r.get("type") == 2],
                "incoming_requests": [r for r in relationships if r.get("type") == 3],
                "outgoing_requests": [r for r in relationships if r.get("type") == 4],
                "total_friends": len(friends),
            }
        return http_request(
            "GET", f"{DISCORD_API_BASE}/users/@me/relationships",
            headers=self._user_headers(), expected=(200,), transform=_shape,
        )

    def user_search_guild_messages(self, guild_id: str, query: str, limit: int = 25) -> Result:
        return http_request(
            "GET", f"{DISCORD_API_BASE}/guilds/{guild_id}/messages/search",
            headers=self._user_headers(),
            params={"content": query, "limit": limit}, expected=(200,), timeout=30,
            transform=lambda d: {
                "total_results": d.get("total_results"),
                "messages": d.get("messages", []),
            },
        )

    # ----- Voice (lazy import + cached manager) -----
    async def _voice_manager(self):
        """Lazy-create + start the DiscordVoiceManager once and reuse it.

        Previous behaviour created a fresh manager + started a new bot
        connection on every voice call, leaking connections.
        """
        if self._voice_mgr is None:
            from . import _discord_voice
            self._voice_mgr = _discord_voice.DiscordVoiceManager(self._bot_token())
        if not getattr(self._voice_mgr, "_running", False):
            await self._voice_mgr.start()
        return self._voice_mgr

    async def join_voice(self, guild_id: str, channel_id: str,
                         self_deaf: bool = False, self_mute: bool = False) -> Result:
        try:
            mgr = await self._voice_manager()
            return await mgr.join_voice(guild_id, channel_id, self_deaf=self_deaf, self_mute=self_mute)
        except ImportError as e:
            return {"error": f"Voice dependencies not installed: {e}"}
        except Exception as e:
            return {"error": str(e)}

    async def leave_voice(self, guild_id: str) -> Result:
        try:
            mgr = await self._voice_manager()
            return await mgr.leave_voice(guild_id)
        except ImportError as e:
            return {"error": f"Voice dependencies not installed: {e}"}
        except Exception as e:
            return {"error": str(e)}

    async def speak_tts(self, guild_id: str, text: str,
                        tts_provider: str = "openai", voice: str = "alloy") -> Result:
        try:
            mgr = await self._voice_manager()
            return await mgr.speak_text(guild_id, text, tts_provider=tts_provider, voice=voice)
        except ImportError as e:
            return {"error": f"Voice dependencies not installed: {e}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_voice_status(self, guild_id: str) -> Result:
        try:
            mgr = await self._voice_manager()
            return mgr.get_voice_status(guild_id)
        except ImportError as e:
            return {"error": f"Voice dependencies not installed: {e}"}
        except Exception as e:
            return {"error": str(e)}
