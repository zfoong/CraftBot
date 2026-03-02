# -*- coding: utf-8 -*-
"""Recall.ai API client — direct HTTP via httpx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from app.external_comms.base import BasePlatformClient
from app.external_comms.credentials import has_credential, load_credential, save_credential, remove_credential
from app.external_comms.registry import register_client

RECALL_API_BASE_US = "https://us-west-2.recall.ai/api/v1"
RECALL_API_BASE_EU = "https://eu-central-1.recall.ai/api/v1"
CREDENTIAL_FILE = "recall.json"


@dataclass
class RecallCredential:
    api_key: str = ""
    region: str = "us"


def _base_url(region: str = "us") -> str:
    return RECALL_API_BASE_EU if region.lower() == "eu" else RECALL_API_BASE_US


@register_client
class RecallClient(BasePlatformClient):
    PLATFORM_ID = "recall"

    def __init__(self):
        super().__init__()
        self._cred: Optional[RecallCredential] = None

    def has_credentials(self) -> bool:
        return has_credential(CREDENTIAL_FILE)

    def _load(self) -> RecallCredential:
        if self._cred is None:
            self._cred = load_credential(CREDENTIAL_FILE, RecallCredential)
        if self._cred is None:
            raise RuntimeError("No Recall credentials. Use /recall login first.")
        return self._cred

    def _headers(self) -> Dict[str, str]:
        cred = self._load()
        return {"Authorization": f"Token {cred.api_key}", "Content-Type": "application/json"}

    async def connect(self) -> None:
        self._load()
        self._connected = True

    async def send_message(self, recipient: str, text: str, **kwargs) -> Dict[str, Any]:
        return self.send_chat_message(recipient, text)

    # ------------------------------------------------------------------
    # Bot management
    # ------------------------------------------------------------------

    def create_bot(
        self,
        meeting_url: str,
        bot_name: str = "Meeting Assistant",
        transcription_options: Optional[Dict[str, Any]] = None,
        chat_options: Optional[Dict[str, Any]] = None,
        recording_mode: str = "speaker_view",
        automatic_leave: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cred = self._load()
        payload: Dict[str, Any] = {"meeting_url": meeting_url, "bot_name": bot_name}
        payload["transcription_options"] = transcription_options or {"provider": "deepgram"}
        if chat_options:
            payload["chat"] = chat_options
        if recording_mode:
            payload["recording_mode"] = recording_mode
        payload["automatic_leave"] = automatic_leave or {
            "waiting_room_timeout": 300,
            "noone_joined_timeout": 300,
            "everyone_left_timeout": 60,
        }
        try:
            r = httpx.post(f"{_base_url(cred.region)}/bot", headers=self._headers(), json=payload, timeout=30)
            if r.status_code in (200, 201):
                data = r.json()
                return {
                    "ok": True,
                    "result": {
                        "bot_id": data.get("id"),
                        "status": data.get("status_changes", [{}])[-1].get("code") if data.get("status_changes") else "starting",
                        "meeting_url": data.get("meeting_url", {}).get("url"),
                        "video_url": data.get("video_url"),
                        "join_at": data.get("join_at"),
                    },
                }
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_bot(self, bot_id: str) -> Dict[str, Any]:
        cred = self._load()
        try:
            r = httpx.get(f"{_base_url(cred.region)}/bot/{bot_id}", headers=self._headers(), timeout=15)
            if r.status_code == 200:
                data = r.json()
                sc = data.get("status_changes", [])
                return {
                    "ok": True,
                    "result": {
                        "bot_id": data.get("id"),
                        "status": sc[-1].get("code") if sc else "unknown",
                        "status_changes": sc,
                        "meeting_url": data.get("meeting_url", {}).get("url"),
                        "video_url": data.get("video_url"),
                        "meeting_participants": data.get("meeting_participants", []),
                        "transcript": data.get("transcript"),
                    },
                }
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def list_bots(self, page_size: int = 50) -> Dict[str, Any]:
        cred = self._load()
        try:
            r = httpx.get(f"{_base_url(cred.region)}/bot", headers=self._headers(), params={"page_size": page_size}, timeout=15)
            if r.status_code == 200:
                data = r.json()
                return {"ok": True, "result": {"bots": data.get("results", []), "count": data.get("count"), "next": data.get("next"), "previous": data.get("previous")}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def delete_bot(self, bot_id: str) -> Dict[str, Any]:
        cred = self._load()
        try:
            r = httpx.delete(f"{_base_url(cred.region)}/bot/{bot_id}", headers=self._headers(), timeout=15)
            if r.status_code in (200, 204):
                return {"ok": True, "result": {"deleted": True, "bot_id": bot_id}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def leave_meeting(self, bot_id: str) -> Dict[str, Any]:
        cred = self._load()
        try:
            r = httpx.post(f"{_base_url(cred.region)}/bot/{bot_id}/leave_call", headers=self._headers(), timeout=15)
            if r.status_code in (200, 204):
                return {"ok": True, "result": {"left": True, "bot_id": bot_id}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def send_chat_message(self, bot_id: str, message: str) -> Dict[str, Any]:
        cred = self._load()
        try:
            r = httpx.post(f"{_base_url(cred.region)}/bot/{bot_id}/send_chat_message", headers=self._headers(), json={"message": message}, timeout=15)
            if r.status_code in (200, 201, 204):
                return {"ok": True, "result": {"sent": True, "message": message}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_transcript(self, bot_id: str) -> Dict[str, Any]:
        cred = self._load()
        try:
            r = httpx.get(f"{_base_url(cred.region)}/bot/{bot_id}/transcript", headers=self._headers(), timeout=30)
            if r.status_code == 200:
                return {"ok": True, "result": {"transcript": r.json()}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_recording(self, bot_id: str) -> Dict[str, Any]:
        result = self.get_bot(bot_id)
        if "ok" in result:
            return {"ok": True, "result": {"video_url": result["result"].get("video_url"), "status": result["result"].get("status")}}
        return result

    def output_audio(self, bot_id: str, audio_data: str, audio_format: str = "wav") -> Dict[str, Any]:
        cred = self._load()
        try:
            r = httpx.post(
                f"{_base_url(cred.region)}/bot/{bot_id}/output_audio",
                headers=self._headers(),
                json={"audio_data": audio_data, "audio_format": audio_format},
                timeout=30,
            )
            if r.status_code in (200, 201, 204):
                return {"ok": True, "result": {"audio_sent": True}}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}
