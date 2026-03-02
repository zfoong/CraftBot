# -*- coding: utf-8 -*-
"""GitHub REST API client — direct HTTP via httpx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from app.external_comms.base import BasePlatformClient
from app.external_comms.credentials import has_credential, load_credential, save_credential, remove_credential
from app.external_comms.registry import register_client

GITHUB_API_BASE = "https://api.github.com"
CREDENTIAL_FILE = "github.json"


@dataclass
class GitHubCredential:
    token: str = ""  # Personal access token or OAuth token
    username: str = ""


@register_client
class GitHubClient(BasePlatformClient):
    PLATFORM_ID = "github"

    def __init__(self):
        super().__init__()
        self._cred: Optional[GitHubCredential] = None

    def has_credentials(self) -> bool:
        return has_credential(CREDENTIAL_FILE)

    def _load(self) -> GitHubCredential:
        if self._cred is None:
            self._cred = load_credential(CREDENTIAL_FILE, GitHubCredential)
        if self._cred is None:
            raise RuntimeError("No GitHub credentials. Use /github login first.")
        return self._cred

    def _headers(self) -> Dict[str, str]:
        cred = self._load()
        return {
            "Authorization": f"Bearer {cred.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def connect(self) -> None:
        self._load()
        self._connected = True

    async def send_message(self, recipient: str, text: str, **kwargs) -> Dict[str, Any]:
        return {"ok": False, "error": "GitHub does not support direct messaging"}

    # ------------------------------------------------------------------
    # User
    # ------------------------------------------------------------------

    def get_authenticated_user(self) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{GITHUB_API_BASE}/user", headers=self._headers(), timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_user(self, username: str) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{GITHUB_API_BASE}/users/{username}", headers=self._headers(), timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Repositories
    # ------------------------------------------------------------------

    def list_repos(self, per_page: int = 30, sort: str = "updated") -> Dict[str, Any]:
        try:
            r = httpx.get(f"{GITHUB_API_BASE}/user/repos", headers=self._headers(),
                          params={"per_page": per_page, "sort": sort}, timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}", headers=self._headers(), timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def create_repo(self, name: str, description: str = "", private: bool = False) -> Dict[str, Any]:
        payload = {"name": name, "description": description, "private": private}
        try:
            r = httpx.post(f"{GITHUB_API_BASE}/user/repos", headers=self._headers(), json=payload, timeout=15)
            if r.status_code == 201:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------

    def list_issues(self, owner: str, repo: str, state: str = "open", per_page: int = 30) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues", headers=self._headers(),
                          params={"state": state, "per_page": per_page}, timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def create_issue(self, owner: str, repo: str, title: str, body: str = "",
                     labels: Optional[List[str]] = None, assignees: Optional[List[str]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
        try:
            r = httpx.post(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues", headers=self._headers(), json=payload, timeout=15)
            if r.status_code == 201:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}", headers=self._headers(), timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def comment_on_issue(self, owner: str, repo: str, issue_number: int, body: str) -> Dict[str, Any]:
        try:
            r = httpx.post(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}/comments",
                           headers=self._headers(), json={"body": body}, timeout=15)
            if r.status_code == 201:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Pull Requests
    # ------------------------------------------------------------------

    def list_pull_requests(self, owner: str, repo: str, state: str = "open", per_page: int = 30) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls", headers=self._headers(),
                          params={"state": state, "per_page": per_page}, timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str,
                            body: str = "", draft: bool = False) -> Dict[str, Any]:
        payload = {"title": title, "head": head, "base": base, "body": body, "draft": draft}
        try:
            r = httpx.post(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls", headers=self._headers(), json=payload, timeout=15)
            if r.status_code == 201:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def get_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pull_number}", headers=self._headers(), timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Notifications / Search
    # ------------------------------------------------------------------

    def list_notifications(self, all_notifications: bool = False, per_page: int = 30) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{GITHUB_API_BASE}/notifications", headers=self._headers(),
                          params={"all": str(all_notifications).lower(), "per_page": per_page}, timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def search_repos(self, query: str, per_page: int = 30) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{GITHUB_API_BASE}/search/repositories", headers=self._headers(),
                          params={"q": query, "per_page": per_page}, timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}

    def search_issues(self, query: str, per_page: int = 30) -> Dict[str, Any]:
        try:
            r = httpx.get(f"{GITHUB_API_BASE}/search/issues", headers=self._headers(),
                          params={"q": query, "per_page": per_page}, timeout=15)
            if r.status_code == 200:
                return {"ok": True, "result": r.json()}
            return {"error": f"API error: {r.status_code}", "details": r.text}
        except Exception as e:
            return {"error": str(e)}
