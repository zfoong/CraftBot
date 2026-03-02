# -*- coding: utf-8 -*-
"""Zoom REST API v2 client — direct HTTP via httpx."""

from __future__ import annotations

import time
from base64 import b64encode
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from app.external_comms.base import BasePlatformClient
from app.external_comms.credentials import has_credential, load_credential, save_credential, remove_credential
from app.external_comms.registry import register_client

ZOOM_API_BASE = "https://api.zoom.us/v2"
ZOOM_OAUTH_BASE = "https://zoom.us/oauth"
CREDENTIAL_FILE = "zoom.json"


@dataclass
class ZoomCredential:
    access_token: str = ""
    refresh_token: str = ""
    token_expiry: float = 0.0
    client_id: str = ""
    client_secret: str = ""


@register_client
class ZoomClient(BasePlatformClient):
    PLATFORM_ID = "zoom"

    def __init__(self):
        super().__init__()
        self._cred: Optional[ZoomCredential] = None

    def has_credentials(self) -> bool:
        return has_credential(CREDENTIAL_FILE)

    def _load(self) -> ZoomCredential:
        if self._cred is None:
            self._cred = load_credential(CREDENTIAL_FILE, ZoomCredential)
        if self._cred is None:
            raise RuntimeError("No Zoom credentials. Use /zoom login first.")
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
        credentials = b64encode(f"{cred.client_id}:{cred.client_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {credentials}", "Content-Type": "application/x-www-form-urlencoded"}
        try:
            r = httpx.post(f"{ZOOM_OAUTH_BASE}/token", data={"grant_type": "refresh_token", "refresh_token": cred.refresh_token}, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                cred.access_token = data["access_token"]
                cred.refresh_token = data.get("refresh_token", cred.refresh_token)
                cred.token_expiry = time.time() + data.get("expires_in", 3600) - 300
                save_credential(CREDENTIAL_FILE, cred)
                self._cred = cred
                return cred.access_token
        except Exception:
            pass
        return None

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._ensure_token()}", "Content-Type": "application/json"}

    async def connect(self) -> None:
        self._load()
        self._connected = True

    async def send_message(self, recipient: str, text: str, **kwargs) -> Dict[str, Any]:
        return {"ok": False, "error": "Zoom does not support direct messaging via REST API"}

    # ------------------------------------------------------------------
    # User operations
    # ------------------------------------------------------------------

    def get_user_profile(self) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{ZOOM_API_BASE}/users/me", headers=self._headers(), timeout=15)
            if r.status_code == 200:
                d = r.json()
                return {"ok": True, "result": {
                    "zoom_user_id": d.get("id"), "email": d.get("email"),
                    "display_name": f'{d.get("first_name", "")} {d.get("last_name", "")}'.strip(),
                    "first_name": d.get("first_name"), "last_name": d.get("last_name"),
                    "account_id": d.get("account_id"), "type": d.get("type"),
                    "pic_url": d.get("pic_url"), "timezone": d.get("timezone"), "pmi": d.get("pmi"),
                }}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def list_users(self, status: str = "active", page_size: int = 30, page_number: int = 1) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{ZOOM_API_BASE}/users", headers=self._headers(), params={"status": status, "page_size": min(page_size, 300), "page_number": page_number}, timeout=15)
            if r.status_code == 200:
                d = r.json()
                return {"ok": True, "result": {"users": d.get("users", []), "page_count": d.get("page_count"), "page_number": d.get("page_number"), "page_size": d.get("page_size"), "total_records": d.get("total_records")}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Meeting operations
    # ------------------------------------------------------------------

    def list_meetings(self, user_id: str = "me", meeting_type: str = "scheduled", page_size: int = 30, page_number: int = 1) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{ZOOM_API_BASE}/users/{user_id}/meetings", headers=self._headers(), params={"type": meeting_type, "page_size": min(page_size, 300), "page_number": page_number}, timeout=15)
            if r.status_code == 200:
                d = r.json()
                return {"ok": True, "result": {"meetings": d.get("meetings", []), "page_count": d.get("page_count"), "page_number": d.get("page_number"), "page_size": d.get("page_size"), "total_records": d.get("total_records")}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_meeting(self, meeting_id: str) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{ZOOM_API_BASE}/meetings/{meeting_id}", headers=self._headers(), timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def create_meeting(
        self,
        topic: str,
        start_time: Optional[str] = None,
        duration: int = 60,
        timezone: str = "UTC",
        agenda: str = "",
        meeting_type: int = 2,
        password: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        user_id: str = "me",
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"topic": topic, "type": meeting_type, "duration": duration, "timezone": timezone, "agenda": agenda}
        if start_time and meeting_type != 1:
            payload["start_time"] = start_time
        if password:
            payload["password"] = password
        payload["settings"] = settings or {"host_video": True, "participant_video": True, "join_before_host": False, "mute_upon_entry": False, "waiting_room": True, "audio": "both", "auto_recording": "none"}
        try:
            r = httpx.post(f"{ZOOM_API_BASE}/users/{user_id}/meetings", headers=self._headers(), json=payload, timeout=15)
            if r.status_code in (200, 201):
                d = r.json()
                return {"ok": True, "result": {"meeting_id": d.get("id"), "topic": d.get("topic"), "start_time": d.get("start_time"), "duration": d.get("duration"), "timezone": d.get("timezone"), "join_url": d.get("join_url"), "start_url": d.get("start_url"), "password": d.get("password"), "host_email": d.get("host_email")}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def update_meeting(self, meeting_id: str, **kwargs) -> Dict[str, Any]:
        payload = {k: v for k, v in kwargs.items() if v is not None and k in ("topic", "start_time", "duration", "timezone", "agenda", "password", "settings")}
        try:
            r = httpx.patch(f"{ZOOM_API_BASE}/meetings/{meeting_id}", headers=self._headers(), json=payload, timeout=15)
            if r.status_code == 204:
                return {"ok": True, "result": {"meeting_id": meeting_id, "updated": True}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def delete_meeting(self, meeting_id: str, occurrence_id: Optional[str] = None, schedule_for_reminder: bool = True) -> Dict[str, Any]:
        params: Dict[str, str] = {}
        if occurrence_id:
            params["occurrence_id"] = occurrence_id
        if not schedule_for_reminder:
            params["schedule_for_reminder"] = "false"
        try:
            r = httpx.delete(f"{ZOOM_API_BASE}/meetings/{meeting_id}", headers=self._headers(), params=params, timeout=15)
            if r.status_code == 204:
                return {"ok": True, "result": {"meeting_id": meeting_id, "deleted": True}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_meeting_invitation(self, meeting_id: str) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{ZOOM_API_BASE}/meetings/{meeting_id}/invitation", headers=self._headers(), timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": {"invitation": r.json().get("invitation")}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_upcoming_meetings(self, user_id: str = "me", page_size: int = 30) -> Dict[str, Any]:
        return self.list_meetings(user_id=user_id, meeting_type="upcoming", page_size=page_size)

    def get_scheduled_meetings(self, user_id: str = "me", page_size: int = 30) -> Dict[str, Any]:
        return self.list_meetings(user_id=user_id, meeting_type="scheduled", page_size=page_size)

    def get_live_meetings(self, user_id: str = "me") -> Dict[str, Any]:
        return self.list_meetings(user_id=user_id, meeting_type="live")
