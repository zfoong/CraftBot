# -*- coding: utf-8 -*-
"""
app.external_comms.platforms.whatsapp_web

WhatsApp Web platform client — uses Playwright (headless Chrome) via the
helper functions in ``app.external_comms.platforms.whatsapp_web_helpers``.

Unlike most platform clients this one does **not** hit an HTTP API.
Every operation is carried out by driving a real Chrome browser session that
is logged in to WhatsApp Web.  Session management, QR-code pairing, and
low-level browser interaction are all handled by the helpers; this module
only exposes a high-level ``BasePlatformClient`` interface on top of them.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.external_comms.base import BasePlatformClient, PlatformMessage, MessageCallback
from app.external_comms.credentials import has_credential, load_credential, save_credential, remove_credential
from app.external_comms.registry import register_client

try:
    from app.logger import logger
except Exception:
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


CREDENTIAL_FILE = "whatsapp_web.json"


@dataclass
class WhatsAppWebCredential:
    session_id: str = ""


# ---------------------------------------------------------------------------
# Platform client
# ---------------------------------------------------------------------------

@register_client
class WhatsAppWebClient(BasePlatformClient):
    """
    WhatsApp Web client backed by Playwright browser automation.

    All heavy lifting is delegated to the helper functions in
    ``app.external_comms.platforms.whatsapp_web_helpers``.
    Imports are done lazily inside each method so that Playwright is only
    required at call time, not at import time.
    """

    PLATFORM_ID = "whatsapp_web"

    # Polling tunables (used by the listener loop)
    POLL_INTERVAL: int = 10   # seconds between polling cycles
    RETRY_DELAY: int = 5      # seconds to wait after an error

    def __init__(self) -> None:
        super().__init__()
        self._cred: Optional[WhatsAppWebCredential] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._seen_fingerprints: set = set()  # dedup: "chat|sender|text|timestamp"
        self._catchup_done: bool = False       # first poll is silent catchup

    # ------------------------------------------------------------------
    # Credential helpers
    # ------------------------------------------------------------------

    def has_credentials(self) -> bool:
        return has_credential(CREDENTIAL_FILE)

    def _load(self) -> WhatsAppWebCredential:
        if self._cred is None:
            self._cred = load_credential(CREDENTIAL_FILE, WhatsAppWebCredential)
        if self._cred is None:
            raise RuntimeError("No WhatsApp Web credentials found. Please log in first.")
        return self._cred

    @property
    def session_id(self) -> str:
        return self._load().session_id

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """Verify that the stored session is usable."""
        cred = self._load()
        status = await self.get_session_status()
        if status is None:
            raise RuntimeError(
                f"WhatsApp Web session '{cred.session_id}' not found or not connected."
            )
        self._connected = True

    async def disconnect(self) -> None:
        """Stop listening (if active) and mark as disconnected."""
        await super().disconnect()

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    async def send_message(self, recipient: str, text: str, **kwargs) -> Dict[str, Any]:
        """
        Send a text message to *recipient* (phone number or JID).

        Delegates to ``send_whatsapp_web_message``.
        """
        from app.external_comms.platforms.whatsapp_web_helpers import (
            send_whatsapp_web_message,
        )

        return await send_whatsapp_web_message(
            session_id=self.session_id,
            to=recipient,
            message=text,
        )

    async def send_media(
        self,
        recipient: str,
        media_path: str,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a media file to *recipient*.

        Delegates to ``send_whatsapp_web_media``.
        """
        from app.external_comms.platforms.whatsapp_web_helpers import (
            send_whatsapp_web_media,
        )

        return await send_whatsapp_web_media(
            session_id=self.session_id,
            to=recipient,
            media_path=media_path,
            caption=caption,
        )

    # ------------------------------------------------------------------
    # Chat / contact queries
    # ------------------------------------------------------------------

    async def get_chat_messages(
        self,
        phone_number: str,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Retrieve recent messages from a specific chat.

        Delegates to ``get_whatsapp_web_chat_messages``.
        """
        from app.external_comms.platforms.whatsapp_web_helpers import (
            get_whatsapp_web_chat_messages,
        )

        return await get_whatsapp_web_chat_messages(
            session_id=self.session_id,
            phone_number=phone_number,
            limit=limit,
        )

    async def get_unread_chats(self) -> Dict[str, Any]:
        """
        Return a list of chats that currently have unread messages.

        Delegates to ``get_whatsapp_web_unread_chats``.
        """
        from app.external_comms.platforms.whatsapp_web_helpers import (
            get_whatsapp_web_unread_chats,
        )

        return await get_whatsapp_web_unread_chats(
            session_id=self.session_id,
        )

    async def search_contact(self, name: str) -> Dict[str, Any]:
        """
        Resolve a contact *name* to a phone number.

        Delegates to ``get_whatsapp_web_contact_phone``.
        """
        from app.external_comms.platforms.whatsapp_web_helpers import (
            get_whatsapp_web_contact_phone,
        )

        return await get_whatsapp_web_contact_phone(
            session_id=self.session_id,
            contact_name=name,
        )

    async def get_session_status(self) -> Optional[Dict[str, Any]]:
        """
        Return the current status of the underlying browser session.

        Delegates to ``get_session_status``.
        """
        from app.external_comms.platforms.whatsapp_web_helpers import (
            get_session_status,
        )

        return await get_session_status(
            session_id=self.session_id,
        )

    # ------------------------------------------------------------------
    # Listening (polling for incoming messages)
    # ------------------------------------------------------------------

    @property
    def supports_listening(self) -> bool:
        return True

    async def start_listening(self, callback: MessageCallback) -> None:
        """
        Begin polling WhatsApp Web for unread messages.

        Before starting the poll loop, ensures a Playwright browser session
        is active on the current event loop (reconnects from persisted profile
        if needed — e.g. after agent restart or when the login was done on a
        separate thread).

        Raises RuntimeError if the session cannot be established.
        """
        if self._listening:
            return

        # Ensure we have an active Playwright session on *this* event loop.
        # The login flow creates the session on a background thread whose event
        # loop is closed afterwards, making the Playwright page unusable.
        # We always clear any stale in-memory session and reconnect from the
        # persisted browser profile so the new browser runs on the current loop.
        sid = self.session_id
        from app.external_comms.platforms.whatsapp_web_helpers import (
            get_whatsapp_web_manager,
            reconnect_whatsapp_web_session,
        )

        manager = get_whatsapp_web_manager()

        # Remove any stale in-memory session so reconnect_session actually
        # launches a fresh browser on the current event loop.
        if sid in manager._sessions:
            logger.info(f"[WhatsApp Web] Clearing stale in-memory session {sid}")
            manager._sessions.pop(sid, None)
            manager._pages.pop(sid, None)
            # Try to close the old browser gracefully (may fail if event loop is dead)
            old_browser = manager._browsers.pop(sid, None)
            if old_browser:
                try:
                    pw, ctx = old_browser
                    await ctx.close()
                    await pw.stop()
                except Exception:
                    pass  # Expected — old event loop is likely closed

        logger.info(f"[WhatsApp Web] Reconnecting session {sid} for listener...")
        result = await reconnect_whatsapp_web_session(
            session_id=sid,
            user_id="local",
        )
        if not result.get("success") and result.get("status") != "connected":
            error = result.get("error", "unknown")
            logger.warning(f"[WhatsApp Web] Could not reconnect session {sid}: {error}")
            raise RuntimeError(f"WhatsApp Web session not connected: {error}")

        self._message_callback = callback
        self._listening = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info(f"[WhatsApp Web] Listener started for session: {sid}")

    async def stop_listening(self) -> None:
        """Cancel the polling task and clean up."""
        if not self._listening:
            return

        self._listening = False

        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

        self._poll_task = None
        logger.info("[WhatsApp Web] Listener stopped")

    # -- internal polling machinery --------------------------------------

    async def _poll_loop(self) -> None:
        """Continuously poll for new messages while ``_listening`` is True."""
        logger.info("[WhatsApp Web] Poll loop started — running initial catchup")
        # Catchup: record everything currently unread so we don't flood on start
        try:
            await self._check_for_messages()
            fingerprints_caught = len(self._seen_fingerprints)
            self._catchup_done = True
            logger.info(f"[WhatsApp Web] Catchup complete — {fingerprints_caught} existing message(s) marked seen")
        except Exception as exc:
            logger.error(f"[WhatsApp Web] Catchup error: {exc}", exc_info=True)
            self._catchup_done = True  # proceed anyway so we don't block forever

        cycle = 0
        while self._listening:
            try:
                cycle += 1
                logger.info(f"[WhatsApp Web] Poll cycle {cycle}")
                await self._check_for_messages()
                await asyncio.sleep(self.POLL_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"[WhatsApp Web] Poll error (cycle {cycle}): {exc}", exc_info=True)
                await asyncio.sleep(self.RETRY_DELAY)
        logger.info("[WhatsApp Web] Poll loop exited")

    async def _check_for_messages(self) -> None:
        """Fetch unread chats and dispatch new incoming messages.

        The helpers return Playwright-scraped data in this format:
        - get_unread_chats: {"success": bool, "unread_chats": [{"name": str, "unread_count": str}]}
        - get_chat_messages_by_name: {"success": bool, "messages": [{"text": str, "is_outgoing": bool, "timestamp": str, "sender": str}]}
        """
        from app.external_comms.platforms.whatsapp_web_helpers import (
            get_whatsapp_web_unread_chats,
            get_whatsapp_web_chat_messages_by_name,
        )

        sid = self.session_id

        unread_result = await get_whatsapp_web_unread_chats(session_id=sid)
        if not unread_result.get("success"):
            logger.warning(f"[WhatsApp Web] get_unread_chats failed: {unread_result.get('error', 'unknown')}")
            return

        unread_chats: List[Dict[str, Any]] = unread_result.get("unread_chats", [])
        if unread_chats:
            logger.info(f"[WhatsApp Web] Found {len(unread_chats)} unread chat(s): {[c.get('name') for c in unread_chats]}")

        for chat in unread_chats:
            chat_name: str = chat.get("name", "")
            unread_count_str: str = str(chat.get("unread_count", "0"))
            detection_source: str = chat.get("source", "badge")

            if not chat_name:
                continue

            try:
                unread_count = int(unread_count_str)
            except (ValueError, TypeError):
                unread_count = 1

            if unread_count == 0:
                continue

            # For preview-change detection (self-messages), only fetch
            # the last few messages since we don't have a real unread count.
            fetch_limit = unread_count + 5 if detection_source == "badge" else 3

            # Fetch recent messages by clicking the chat in the sidebar
            messages_result = await get_whatsapp_web_chat_messages_by_name(
                session_id=sid,
                chat_name=chat_name,
                limit=fetch_limit,
            )

            if not messages_result.get("success"):
                continue

            all_messages: List[Dict[str, Any]] = messages_result.get("messages", [])

            # Only process the tail of the message list
            messages = all_messages[-unread_count:] if len(all_messages) > unread_count else all_messages

            # Self-message detection: preview_change means the user sent
            # themselves a message (all messages appear as outgoing).
            is_self_chat = (detection_source == "preview_change")

            for msg in messages:
                # Skip outgoing messages unless this is a self-chat
                if msg.get("is_outgoing", False) and not is_self_chat:
                    continue

                text = msg.get("text", "")
                if not text or text.startswith("["):
                    # Skip empty or media-only messages ([Image], [Video], etc.)
                    continue

                # Deduplicate: build a fingerprint from chat + sender + text
                sender = msg.get("sender", chat_name)
                timestamp_str = msg.get("timestamp", "")
                msg_fingerprint = f"{chat_name}|{sender}|{text}|{timestamp_str}"

                if msg_fingerprint in self._seen_fingerprints:
                    continue
                self._seen_fingerprints.add(msg_fingerprint)

                # During catchup we only record fingerprints, don't dispatch
                if not self._catchup_done:
                    continue

                ts: Optional[datetime] = None
                if timestamp_str:
                    try:
                        ts = datetime.now(tz=timezone.utc)
                    except Exception:
                        pass

                platform_msg = PlatformMessage(
                    platform=self.PLATFORM_ID,
                    sender_id=chat_name,
                    sender_name=sender if sender != "me" else chat_name,
                    text=text,
                    channel_id=chat_name,
                    channel_name=chat_name,
                    message_id=f"{chat_name}_{timestamp_str}_{hash(text) & 0xFFFFFFFF:08x}",
                    timestamp=ts,
                    raw={
                        "source": "WhatsApp Web",
                        "integrationType": "whatsapp_web",
                        "is_self_message": is_self_chat,
                        "contactId": chat_name,
                        "contactName": sender if sender != "me" else chat_name,
                        "messageBody": text,
                        "chatId": chat_name,
                        "chatName": chat_name,
                        "timestamp": timestamp_str,
                    },
                )

                if self._message_callback:
                    await self._message_callback(platform_msg)

                logger.info(f"[WhatsApp Web] Dispatched message from {sender} in {chat_name}: {text[:50]}...")
