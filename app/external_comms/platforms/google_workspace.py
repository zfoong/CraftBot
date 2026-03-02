# -*- coding: utf-8 -*-
"""Google Workspace client — Gmail + Calendar + Drive via httpx."""

from __future__ import annotations

import base64
import mimetypes
import os
import time
from dataclasses import dataclass
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import httpx

from app.external_comms.base import BasePlatformClient
from app.external_comms.credentials import has_credential, load_credential, save_credential, remove_credential
from app.external_comms.registry import register_client

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
CREDENTIAL_FILE = "google.json"


@dataclass
class GoogleCredential:
    access_token: str = ""
    refresh_token: str = ""
    token_expiry: float = 0.0
    client_id: str = ""
    client_secret: str = ""
    email: str = ""


@register_client
class GoogleWorkspaceClient(BasePlatformClient):
    PLATFORM_ID = "google_workspace"

    def __init__(self):
        super().__init__()
        self._cred: Optional[GoogleCredential] = None

    # ------------------------------------------------------------------
    # Credential helpers
    # ------------------------------------------------------------------

    def has_credentials(self) -> bool:
        return has_credential(CREDENTIAL_FILE)

    def _load(self) -> GoogleCredential:
        if self._cred is None:
            self._cred = load_credential(CREDENTIAL_FILE, GoogleCredential)
        if self._cred is None:
            raise RuntimeError("No Google credentials. Configure google.json first.")
        return self._cred

    def _ensure_token(self) -> str:
        """Return a valid access token, refreshing if expired."""
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
        try:
            r = httpx.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": cred.client_id,
                    "client_secret": cred.client_secret,
                    "refresh_token": cred.refresh_token,
                    "grant_type": "refresh_token",
                },
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                cred.access_token = data["access_token"]
                cred.token_expiry = time.time() + data.get("expires_in", 3600) - 60
                save_credential(CREDENTIAL_FILE, cred)
                self._cred = cred
                return cred.access_token
        except Exception:
            pass
        return None

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._ensure_token()}",
            "Content-Type": "application/json",
        }

    def _auth_header(self) -> Dict[str, str]:
        """Authorization header only (no Content-Type)."""
        return {"Authorization": f"Bearer {self._ensure_token()}"}

    # ------------------------------------------------------------------
    # BasePlatformClient interface
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        self._load()
        self._connected = True

    async def send_message(self, recipient: str, text: str, **kwargs) -> Dict[str, Any]:
        """Send an email (maps the generic interface to send_email)."""
        subject = kwargs.get("subject", "")
        result = self.send_email(to=recipient, subject=subject, body=text)
        return result

    # ==================================================================
    # Gmail
    # ==================================================================

    @staticmethod
    def _encode_email(
        to_email: str,
        from_email: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
    ) -> str:
        """Build a MIME message and return it as a base64 URL-safe string."""
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
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{os.path.basename(file_path)}"',
                    )
                    msg.attach(part)

        return base64.urlsafe_b64encode(msg.as_bytes()).decode()

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send an email via the Gmail API."""
        cred = self._load()
        sender = from_email or cred.email
        raw = self._encode_email(to, sender, subject, body, attachments)
        try:
            r = httpx.post(
                f"{GMAIL_API_BASE}/users/me/messages/send",
                headers=self._headers(),
                json={"raw": raw},
                timeout=15,
            )
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def list_emails(self, n: int = 5, unread_only: bool = True) -> Dict[str, Any]:
        """List the top *n* recent emails from the inbox."""
        params: Dict[str, Any] = {
            "maxResults": n,
            "labelIds": ["INBOX"],
        }
        if unread_only:
            params["q"] = "is:unread"
        try:
            r = httpx.get(
                f"{GMAIL_API_BASE}/users/me/messages",
                headers=self._auth_header(),
                params=params,
                timeout=15,
            )
            if r.status_code == 200:
                messages = r.json().get("messages", [])
                return {"ok": True, "result": messages}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_email(self, message_id: str, full_body: bool = False) -> Dict[str, Any]:
        """Get detailed information about a specific email message."""
        format_type = "full" if full_body else "metadata"
        params = {
            "format": format_type,
            "metadataHeaders": ["From", "To", "Subject", "Date"],
        }
        try:
            r = httpx.get(
                f"{GMAIL_API_BASE}/users/me/messages/{message_id}",
                headers=self._auth_header(),
                params=params,
                timeout=15,
            )
            if r.status_code != 200:
                return {"error": f"API error: {r.status_code}", "details": r.text}

            msg = r.json()
            email_info: Dict[str, Any] = {
                "id": msg.get("id"),
                "snippet": msg.get("snippet", ""),
                "headers": {
                    h["name"]: h["value"]
                    for h in msg.get("payload", {}).get("headers", [])
                },
            }

            if full_body and "parts" in msg.get("payload", {}):
                for part in msg["payload"]["parts"]:
                    if (
                        part.get("mimeType") == "text/plain"
                        and "data" in part.get("body", {})
                    ):
                        data = part["body"]["data"]
                        email_info["body"] = base64.urlsafe_b64decode(
                            data.encode("ASCII")
                        ).decode("utf-8")
                        break

            return {"ok": True, "result": email_info}
        except Exception as e:
            return {"error": str(e)}

    def read_top_emails(self, n: int = 5, full_body: bool = False) -> Dict[str, Any]:
        """Convenience: list recent emails then fetch details for each."""
        listing = self.list_emails(n=n, unread_only=False)
        if "error" in listing:
            return listing
        messages = listing.get("result", [])
        emails: List[Dict[str, Any]] = []
        for msg in messages:
            detail = self.get_email(msg["id"], full_body=full_body)
            if "error" not in detail:
                emails.append(detail.get("result", detail))
            else:
                emails.append(detail)
        return {"ok": True, "result": emails}

    # ==================================================================
    # Calendar
    # ==================================================================

    def create_meet_event(
        self,
        calendar_id: str = "primary",
        event_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a calendar event (with optional Google Meet conference)."""
        try:
            r = httpx.post(
                f"{CALENDAR_API_BASE}/calendars/{calendar_id}/events",
                headers=self._headers(),
                params={"conferenceDataVersion": 1},
                json=event_data or {},
                timeout=15,
            )
            if r.status_code in (200, 201):
                return {"ok": True, "result": r.json()}
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            return {"error": f"API error: {r.status_code}", "details": detail}
        except Exception as e:
            return {"error": str(e)}

    def check_availability(
        self,
        calendar_id: str = "primary",
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Query Google Calendar freebusy endpoint."""
        payload = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": calendar_id}],
        }
        try:
            r = httpx.post(
                f"{CALENDAR_API_BASE}/freeBusy",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            return {"error": f"API error: {r.status_code}", "details": detail}
        except Exception as e:
            return {"error": str(e)}

    # ==================================================================
    # Drive
    # ==================================================================

    def list_drive_files(
        self,
        folder_id: str,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List files inside a Drive folder."""
        params = {
            "q": f"'{folder_id}' in parents and trashed = false",
            "fields": fields or "files(id,name,mimeType,parents)",
        }
        try:
            r = httpx.get(
                f"{DRIVE_API_BASE}/files",
                headers=self._auth_header(),
                params=params,
                timeout=15,
            )
            if r.status_code == 200:
                return {"ok": True, "result": r.json().get("files", [])}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def create_drive_folder(
        self,
        name: str,
        parent_folder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new folder in Google Drive."""
        payload: Dict[str, Any] = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_folder_id:
            payload["parents"] = [parent_folder_id]
        try:
            r = httpx.post(
                f"{DRIVE_API_BASE}/files",
                headers=self._headers(),
                json=payload,
                timeout=15,
            )
            if r.status_code in (200, 201):
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_drive_file(
        self,
        file_id: str,
        fields: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get metadata for a single Drive file."""
        params = {"fields": fields or "id,parents"}
        try:
            r = httpx.get(
                f"{DRIVE_API_BASE}/files/{file_id}",
                headers=self._auth_header(),
                params=params,
                timeout=15,
            )
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def move_drive_file(
        self,
        file_id: str,
        add_parents: str,
        remove_parents: str,
    ) -> Dict[str, Any]:
        """Move a Drive file between folders."""
        params: Dict[str, str] = {
            "addParents": add_parents,
            "fields": "id,parents",
        }
        if remove_parents:
            params["removeParents"] = remove_parents
        try:
            r = httpx.patch(
                f"{DRIVE_API_BASE}/files/{file_id}",
                headers=self._auth_header(),
                params=params,
                timeout=15,
            )
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def find_drive_folder_by_name(
        self,
        name: str,
        parent_folder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Find a Drive folder by name (optionally scoped to a parent)."""
        q_parts = [
            f"name = '{name}'",
            "mimeType = 'application/vnd.google-apps.folder'",
            "trashed = false",
        ]
        if parent_folder_id:
            q_parts.append(f"'{parent_folder_id}' in parents")
        params = {
            "q": " and ".join(q_parts),
            "fields": "files(id,name)",
        }
        try:
            r = httpx.get(
                f"{DRIVE_API_BASE}/files",
                headers=self._auth_header(),
                params=params,
                timeout=15,
            )
            if r.status_code == 200:
                files = r.json().get("files", [])
                folder = files[0] if files else None
                return {"ok": True, "result": folder}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}
