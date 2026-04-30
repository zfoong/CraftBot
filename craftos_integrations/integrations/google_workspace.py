# -*- coding: utf-8 -*-
"""Google Workspace integration — Gmail + Calendar + Drive (OAuth + PKCE)."""
from __future__ import annotations

import asyncio
import base64
import mimetypes
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple

from .. import (
    BasePlatformClient,
    IntegrationHandler,
    IntegrationSpec,
    OAuthFlow,
    PlatformMessage,
    has_credential,
    load_credential,
    register_client,
    register_handler,
    remove_credential,
    save_credential,
)
from ..config import ConfigStore
from ..helpers import Result, arequest, request as http_request
from ..logger import get_logger

logger = get_logger(__name__)

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GOOGLE_SCOPES = (
    "https://www.googleapis.com/auth/gmail.modify "
    "https://www.googleapis.com/auth/calendar "
    "https://www.googleapis.com/auth/drive "
    "https://www.googleapis.com/auth/contacts.readonly "
    "https://www.googleapis.com/auth/userinfo.email "
    "https://www.googleapis.com/auth/userinfo.profile "
    "https://www.googleapis.com/auth/youtube.readonly "
    "https://www.googleapis.com/auth/youtube.force-ssl"
)

POLL_INTERVAL = 5
RETRY_DELAY = 10


@dataclass
class GoogleCredential:
    access_token: str = ""
    refresh_token: str = ""
    token_expiry: float = 0.0
    client_id: str = ""
    client_secret: str = ""
    email: str = ""


GOOGLE = IntegrationSpec(
    name="google",
    cred_class=GoogleCredential,
    cred_file="google.json",
    platform_id="google_workspace",
)


# ════════════════════════════════════════════════════════════════════════
# Handler
# ════════════════════════════════════════════════════════════════════════

@register_handler(GOOGLE.name)
class GoogleHandler(IntegrationHandler):
    spec = GOOGLE
    display_name = "Google Workspace"
    description = "Gmail, Calendar, Drive"
    auth_type = "oauth"
    icon = "google"
    fields: List = []

    oauth = OAuthFlow(
        client_id_key="GOOGLE_CLIENT_ID",
        client_secret_key="GOOGLE_CLIENT_SECRET",
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url=GOOGLE_TOKEN_URL,
        userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
        scopes=GOOGLE_SCOPES,
        use_pkce=True,
        extra_auth_params={"access_type": "offline", "prompt": "consent"},
    )

    async def login(self, args: List[str]) -> Tuple[bool, str]:
        result = await self.oauth.run()
        if "error" in result and not result.get("access_token"):
            return False, f"Google OAuth failed: {result['error']}"

        info = result.get("userinfo", {})
        save_credential(self.spec.cred_file, GoogleCredential(
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token", ""),
            token_expiry=time.time() + result.get("expires_in", 3600),
            client_id=ConfigStore.get_oauth("GOOGLE_CLIENT_ID"),
            client_secret=ConfigStore.get_oauth("GOOGLE_CLIENT_SECRET"),
            email=info.get("email", ""),
        ))
        return True, f"Google connected as {info.get('email')}"

    async def logout(self, args: List[str]) -> Tuple[bool, str]:
        if not has_credential(self.spec.cred_file):
            return False, "No Google credentials found."
        remove_credential(self.spec.cred_file)
        return True, "Removed Google credential."

    async def status(self) -> Tuple[bool, str]:
        if not has_credential(self.spec.cred_file):
            return True, "Google: Not connected"
        cred = load_credential(self.spec.cred_file, GoogleCredential)
        email = cred.email if cred else "unknown"
        return True, f"Google: Connected\n  - {email}"


# ════════════════════════════════════════════════════════════════════════
# Client
# ════════════════════════════════════════════════════════════════════════

@register_client
class GoogleWorkspaceClient(BasePlatformClient):
    spec = GOOGLE
    PLATFORM_ID = GOOGLE.platform_id

    def __init__(self):
        super().__init__()
        self._cred: Optional[GoogleCredential] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._history_id: Optional[str] = None
        self._seen_message_ids: set = set()

    def has_credentials(self) -> bool:
        return has_credential(self.spec.cred_file)

    def _load(self) -> GoogleCredential:
        if self._cred is None:
            self._cred = load_credential(self.spec.cred_file, GoogleCredential)
        if self._cred is None:
            raise RuntimeError("No Google credentials. Configure google.json first.")
        return self._cred

    def _ensure_token(self) -> str:
        cred = self._load()
        if cred.refresh_token and cred.token_expiry and time.time() > cred.token_expiry:
            result = self.refresh_access_token()
            if result:
                return result
        return cred.access_token

    def refresh_access_token(self) -> Optional[str]:
        cred = self._load()
        if not all([cred.client_id, cred.client_secret, cred.refresh_token]):
            return None
        result = http_request("POST", GOOGLE_TOKEN_URL, data={
            "client_id": cred.client_id,
            "client_secret": cred.client_secret,
            "refresh_token": cred.refresh_token,
            "grant_type": "refresh_token",
        }, expected=(200,))
        if "error" in result:
            return None
        data = result["result"]
        cred.access_token = data["access_token"]
        cred.token_expiry = time.time() + data.get("expires_in", 3600) - 60
        save_credential(self.spec.cred_file, cred)
        self._cred = cred
        return cred.access_token

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._ensure_token()}", "Content-Type": "application/json"}

    def _auth_header(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._ensure_token()}"}

    async def connect(self) -> None:
        self._load()
        self._connected = True

    async def send_message(self, recipient: str, text: str, **kwargs) -> Result:
        return self.send_email(to=recipient, subject=kwargs.get("subject", ""), body=text)

    @property
    def supports_listening(self) -> bool:
        return True

    async def start_listening(self, callback) -> None:
        if self._listening:
            return
        self._message_callback = callback
        self._load()

        try:
            profile = await self._async_get_profile()
            self._history_id = profile.get("historyId")
            logger.info(f"[GOOGLE] Gmail profile: {profile.get('emailAddress')}, historyId: {self._history_id}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Gmail: {e}")

        self._listening = True
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop_listening(self) -> None:
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

    async def _async_get_profile(self) -> Dict[str, Any]:
        result = await arequest("GET", f"{GMAIL_API_BASE}/users/me/profile",
                                headers=self._auth_header(), expected=(200,))
        if "error" in result:
            raise RuntimeError(f"Gmail profile {result['error']}")
        return result["result"]

    async def _poll_loop(self) -> None:
        while self._listening:
            try:
                await self._check_history()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[GOOGLE] Poll error: {e}")
                if "404" in str(e) or "historyId" in str(e).lower():
                    try:
                        profile = await self._async_get_profile()
                        self._history_id = profile.get("historyId")
                    except Exception:
                        pass
                await asyncio.sleep(RETRY_DELAY)
                continue
            await asyncio.sleep(POLL_INTERVAL)

    async def _check_history(self) -> None:
        if not self._history_id:
            return
        result = await arequest(
            "GET", f"{GMAIL_API_BASE}/users/me/history",
            headers=self._auth_header(),
            params={"startHistoryId": self._history_id, "historyTypes": "messageAdded", "labelId": "INBOX"},
            expected=(200,),
        )
        if "error" in result:
            if "404" in result["error"]:
                raise RuntimeError("historyId expired (404)")
            logger.warning(f"[GOOGLE] history.list {result['error']}")
            return

        data = result["result"] or {}
        new_history_id = data.get("historyId")
        if new_history_id:
            self._history_id = new_history_id

        new_msg_ids = []
        for record in data.get("history", []):
            for added in record.get("messagesAdded", []):
                msg = added.get("message", {})
                msg_id = msg.get("id", "")
                if msg_id and "INBOX" in msg.get("labelIds", []) and msg_id not in self._seen_message_ids:
                    new_msg_ids.append(msg_id)
                    self._seen_message_ids.add(msg_id)

        if len(self._seen_message_ids) > 500:
            self._seen_message_ids = set(list(self._seen_message_ids)[-200:])

        for msg_id in new_msg_ids:
            try:
                await self._fetch_and_dispatch(msg_id)
            except Exception as e:
                logger.debug(f"[GOOGLE] Error processing message {msg_id}: {e}")

    async def _fetch_and_dispatch(self, msg_id: str) -> None:
        result = await arequest(
            "GET", f"{GMAIL_API_BASE}/users/me/messages/{msg_id}",
            headers=self._auth_header(),
            params=[("format", "metadata"), ("metadataHeaders", "From"),
                    ("metadataHeaders", "Subject"), ("metadataHeaders", "Date")],
            expected=(200,),
        )
        if "error" in result:
            return

        msg = result["result"]
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        from_header = headers.get("From", "")
        subject = headers.get("Subject", "(no subject)")
        snippet = msg.get("snippet", "")

        sender_name = from_header
        sender_email = from_header
        if "<" in from_header and ">" in from_header:
            parts = from_header.rsplit("<", 1)
            sender_name = parts[0].strip().strip('"')
            sender_email = parts[1].rstrip(">").strip()

        cred = self._load()
        if sender_email.lower() == (cred.email or "").lower():
            return

        timestamp = None
        try:
            from email.utils import parsedate_to_datetime
            timestamp = parsedate_to_datetime(headers.get("Date", ""))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
        except Exception:
            pass

        text = f"Subject: {subject}\n{snippet}" if snippet else f"Subject: {subject}"

        if self._message_callback:
            await self._message_callback(PlatformMessage(
                platform=self.spec.platform_id,
                sender_id=sender_email,
                sender_name=sender_name or sender_email,
                text=text,
                channel_id=msg.get("threadId", ""),
                message_id=msg_id,
                timestamp=timestamp,
                raw=msg,
            ))

    # --- Gmail ---
    @staticmethod
    def _encode_email(to_email: str, from_email: str, subject: str, body: str,
                      attachments: Optional[List[str]] = None) -> str:
        msg = MIMEMultipart()
        msg["to"] = to_email
        msg["from"] = from_email
        msg["subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if attachments:
            for file_path in attachments:
                if not os.path.isfile(file_path):
                    continue
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type is None:
                    mime_type = "application/octet-stream"
                maintype, subtype = mime_type.split("/", 1)
                with open(file_path, "rb") as f:
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(file_path)}"')
                    msg.attach(part)

        return base64.urlsafe_b64encode(msg.as_bytes()).decode()

    def send_email(self, to: str, subject: str, body: str,
                   from_email: Optional[str] = None,
                   attachments: Optional[List[str]] = None) -> Result:
        cred = self._load()
        sender = from_email or cred.email
        raw = self._encode_email(to, sender, subject, body, attachments)
        return http_request(
            "POST", f"{GMAIL_API_BASE}/users/me/messages/send",
            headers=self._headers(), json={"raw": raw}, expected=(200,),
        )

    def list_emails(self, n: int = 5, unread_only: bool = True) -> Result:
        params: Dict[str, Any] = {"maxResults": n, "labelIds": ["INBOX"]}
        if unread_only:
            params["q"] = "is:unread"
        return http_request(
            "GET", f"{GMAIL_API_BASE}/users/me/messages",
            headers=self._auth_header(), params=params, expected=(200,),
            transform=lambda d: d.get("messages", []),
        )

    def get_email(self, message_id: str, full_body: bool = False) -> Result:
        format_type = "full" if full_body else "metadata"

        def _shape(msg):
            email_info: Dict[str, Any] = {
                "id": msg.get("id"), "snippet": msg.get("snippet", ""),
                "headers": {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])},
            }
            if full_body and "parts" in msg.get("payload", {}):
                for part in msg["payload"]["parts"]:
                    if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                        email_info["body"] = base64.urlsafe_b64decode(
                            part["body"]["data"].encode("ASCII")
                        ).decode("utf-8")
                        break
            return email_info

        return http_request(
            "GET", f"{GMAIL_API_BASE}/users/me/messages/{message_id}",
            headers=self._auth_header(),
            params={"format": format_type, "metadataHeaders": ["From", "To", "Subject", "Date"]},
            expected=(200,), transform=_shape,
        )

    def read_top_emails(self, n: int = 5, full_body: bool = False) -> Result:
        listing = self.list_emails(n=n, unread_only=False)
        if "error" in listing:
            return listing
        emails: List[Dict[str, Any]] = []
        for msg in listing.get("result", []):
            detail = self.get_email(msg["id"], full_body=full_body)
            emails.append(detail.get("result", detail) if "error" not in detail else detail)
        return {"ok": True, "result": emails}

    # --- Calendar ---
    def create_meet_event(self, calendar_id: str = "primary",
                          event_data: Optional[Dict[str, Any]] = None) -> Result:
        return http_request(
            "POST", f"{CALENDAR_API_BASE}/calendars/{calendar_id}/events",
            headers=self._headers(), params={"conferenceDataVersion": 1},
            json=event_data or {},
        )

    def check_availability(self, calendar_id: str = "primary",
                           time_min: Optional[str] = None,
                           time_max: Optional[str] = None) -> Result:
        return http_request(
            "POST", f"{CALENDAR_API_BASE}/freeBusy",
            headers=self._headers(),
            json={"timeMin": time_min, "timeMax": time_max, "items": [{"id": calendar_id}]},
            expected=(200,),
        )

    # --- Drive ---
    def list_drive_files(self, folder_id: str, fields: Optional[str] = None) -> Result:
        return http_request(
            "GET", f"{DRIVE_API_BASE}/files", headers=self._auth_header(),
            params={
                "q": f"'{folder_id}' in parents and trashed = false",
                "fields": fields or "files(id,name,mimeType,parents)",
            },
            expected=(200,),
            transform=lambda d: d.get("files", []),
        )

    def create_drive_folder(self, name: str, parent_folder_id: Optional[str] = None) -> Result:
        payload: Dict[str, Any] = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
        if parent_folder_id:
            payload["parents"] = [parent_folder_id]
        return http_request(
            "POST", f"{DRIVE_API_BASE}/files", headers=self._headers(),
            json=payload,
        )

    def get_drive_file(self, file_id: str, fields: Optional[str] = None) -> Result:
        return http_request(
            "GET", f"{DRIVE_API_BASE}/files/{file_id}",
            headers=self._auth_header(),
            params={"fields": fields or "id,parents"},
            expected=(200,),
        )

    def move_drive_file(self, file_id: str, add_parents: str, remove_parents: str) -> Result:
        params: Dict[str, str] = {"addParents": add_parents, "fields": "id,parents"}
        if remove_parents:
            params["removeParents"] = remove_parents
        return http_request(
            "PATCH", f"{DRIVE_API_BASE}/files/{file_id}",
            headers=self._auth_header(), params=params, expected=(200,),
        )

    def find_drive_folder_by_name(self, name: str,
                                   parent_folder_id: Optional[str] = None) -> Result:
        q_parts = [
            f"name = '{name}'",
            "mimeType = 'application/vnd.google-apps.folder'",
            "trashed = false",
        ]
        if parent_folder_id:
            q_parts.append(f"'{parent_folder_id}' in parents")
        return http_request(
            "GET", f"{DRIVE_API_BASE}/files", headers=self._auth_header(),
            params={"q": " and ".join(q_parts), "fields": "files(id,name)"},
            expected=(200,),
            transform=lambda d: (d.get("files") or [None])[0],
        )
