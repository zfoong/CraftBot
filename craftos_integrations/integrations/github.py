# -*- coding: utf-8 -*-
"""GitHub integration — handler + client + credential.

This is the canonical example of an integration file:
  - one credential dataclass
  - one IntegrationSpec (referenced by both handler and client = composition)
  - one IntegrationHandler (auth: login/logout/status)
  - one BasePlatformClient (runtime: notification polling, REST API)

To add another integration, copy this file and adapt.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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
from ..helpers import Result, arequest, request as http_request
from ..logger import get_logger

logger = get_logger(__name__)

GITHUB_API = "https://api.github.com"
POLL_INTERVAL = 15
RETRY_DELAY = 30


@dataclass
class GitHubCredential:
    access_token: str = ""
    username: str = ""
    watch_repos: List[str] = field(default_factory=list)
    watch_tag: str = ""


GITHUB = IntegrationSpec(
    name="github",
    cred_class=GitHubCredential,
    cred_file="github.json",
    platform_id="github",
)


# ════════════════════════════════════════════════════════════════════════
# Handler — auth flows
# ════════════════════════════════════════════════════════════════════════

@register_handler(GITHUB.name)
class GitHubHandler(IntegrationHandler):
    spec = GITHUB
    display_name = "GitHub"
    description = "Repositories, issues, and pull requests"
    auth_type = "token"
    fields = [
        {"key": "access_token", "label": "Personal Access Token", "placeholder": "ghp_...", "password": True},
    ]

    async def login(self, args: List[str]) -> Tuple[bool, str]:
        if not args:
            return False, (
                "Usage: /github login <personal_access_token>\n"
                "Generate one at: https://github.com/settings/tokens"
            )
        token = args[0].strip()

        result = http_request(
            "GET", "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            expected=(200,),
        )
        if "error" in result:
            return False, f"GitHub auth failed: {result['error']}"
        data = result["result"]

        save_credential(self.spec.cred_file, GitHubCredential(
            access_token=token,
            username=data.get("login", ""),
        ))
        return True, f"GitHub connected as @{data.get('login')} ({data.get('name', '')})"

    async def logout(self, args: List[str]) -> Tuple[bool, str]:
        if not has_credential(self.spec.cred_file):
            return False, "No GitHub credentials found."
        try:
            from ..manager import get_external_comms_manager
            manager = get_external_comms_manager()
            if manager:
                await manager.stop_platform(self.spec.platform_id)
        except Exception:
            pass
        remove_credential(self.spec.cred_file)
        return True, "Removed GitHub credential."

    async def status(self) -> Tuple[bool, str]:
        if not has_credential(self.spec.cred_file):
            return True, "GitHub: Not connected"
        cred = load_credential(self.spec.cred_file, GitHubCredential)
        if not cred:
            return True, "GitHub: Not connected"
        username = cred.username or "unknown"
        tag_info = f" [tag: {cred.watch_tag}]" if cred.watch_tag else ""
        repos_info = f" [repos: {', '.join(cred.watch_repos)}]" if cred.watch_repos else ""
        return True, f"GitHub: Connected\n  - @{username}{tag_info}{repos_info}"


# ════════════════════════════════════════════════════════════════════════
# Client — runtime: REST API + notification polling
# ════════════════════════════════════════════════════════════════════════

@register_client
class GitHubClient(BasePlatformClient):
    spec = GITHUB
    PLATFORM_ID = GITHUB.platform_id

    def __init__(self) -> None:
        super().__init__()
        self._cred: Optional[GitHubCredential] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._last_modified: Optional[str] = None
        self._seen_ids: set = set()
        self._catchup_done: bool = False

    def has_credentials(self) -> bool:
        return has_credential(self.spec.cred_file)

    def _load(self) -> GitHubCredential:
        if self._cred is None:
            self._cred = load_credential(self.spec.cred_file, GitHubCredential)
        if self._cred is None:
            raise RuntimeError("No GitHub credentials. Use /github login first.")
        return self._cred

    def _headers(self) -> Dict[str, str]:
        cred = self._load()
        return {
            "Authorization": f"Bearer {cred.access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def connect(self) -> None:
        self._load()
        self._connected = True

    async def send_message(self, recipient: str, text: str, **kwargs) -> Result:
        try:
            repo_part, number = recipient.rsplit("#", 1)
            return await self.create_comment(repo_part.strip(), int(number), text)
        except (ValueError, IndexError):
            return {"error": f"Invalid recipient format. Use 'owner/repo#number', got: {recipient}"}

    # ----- Watch tag / repos -----

    def get_watch_tag(self) -> str:
        return self._load().watch_tag

    def set_watch_tag(self, tag: str) -> None:
        cred = self._load()
        cred.watch_tag = tag.strip()
        save_credential(self.spec.cred_file, cred)
        self._cred = cred
        logger.info(f"[GITHUB] Watch tag set to: {cred.watch_tag or '(disabled)'}")

    def get_watch_repos(self) -> List[str]:
        return list(self._load().watch_repos)

    def set_watch_repos(self, repos: List[str]) -> None:
        cred = self._load()
        cred.watch_repos = [r.strip() for r in repos if r.strip()]
        save_credential(self.spec.cred_file, cred)
        self._cred = cred
        logger.info(f"[GITHUB] Watch repos set to: {cred.watch_repos or '(all)'}")

    # ----- Listening -----

    @property
    def supports_listening(self) -> bool:
        return True

    async def start_listening(self, callback) -> None:
        if self._listening:
            return

        self._message_callback = callback
        self._load()

        me = await self.get_authenticated_user()
        if "error" in me:
            raise RuntimeError(f"Invalid GitHub token: {me.get('error')}")

        username = me.get("result", {}).get("login", "unknown")
        logger.info(f"[GITHUB] Authenticated as: {username}")

        cred = self._load()
        if cred.username != username:
            cred.username = username
            save_credential(self.spec.cred_file, cred)
            self._cred = cred

        self._last_modified = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
        self._catchup_done = True
        self._listening = True
        self._poll_task = asyncio.create_task(self._poll_loop())

        tag_info = cred.watch_tag or "(disabled — all events)"
        repos_info = ", ".join(cred.watch_repos) if cred.watch_repos else "(all repos)"
        logger.info(f"[GITHUB] Poller started — tag: {tag_info} | repos: {repos_info}")

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
        logger.info("[GITHUB] Poller stopped")

    async def _poll_loop(self) -> None:
        while self._listening:
            try:
                await self._check_notifications()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[GITHUB] Poll error: {e}")
                await asyncio.sleep(RETRY_DELAY)
                continue
            await asyncio.sleep(POLL_INTERVAL)

    async def _check_notifications(self) -> None:
        headers = self._headers()
        if self._last_modified:
            headers["If-Modified-Since"] = self._last_modified

        cred = self._load()

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}/notifications",
                headers=headers,
                params={"all": "false", "participating": "true"},
                timeout=30,
            )

            if resp.status_code == 304:
                return
            if resp.status_code == 401:
                logger.warning("[GITHUB] Authentication expired (401)")
                return
            if resp.status_code != 200:
                logger.warning(f"[GITHUB] Notifications API error: {resp.status_code}")
                return

            lm = resp.headers.get("Last-Modified")
            if lm:
                self._last_modified = lm

            notifications = resp.json()

            for notif in notifications:
                notif_id = notif.get("id", "")
                if notif_id in self._seen_ids:
                    continue
                self._seen_ids.add(notif_id)

                repo_full = notif.get("repository", {}).get("full_name", "")
                if cred.watch_repos and repo_full not in cred.watch_repos:
                    continue

                await self._dispatch_notification(client, notif)

            if len(self._seen_ids) > 500:
                self._seen_ids = set(list(self._seen_ids)[-200:])

    async def _dispatch_notification(self, client: httpx.AsyncClient, notif: Dict[str, Any]) -> None:
        if not self._message_callback:
            return

        cred = self._load()
        reason = notif.get("reason", "")
        subject = notif.get("subject", {})
        subject_type = subject.get("type", "")
        subject_title = subject.get("title", "")
        repo = notif.get("repository", {})
        repo_full = repo.get("full_name", "")

        latest_comment_url = subject.get("latest_comment_url", "")
        comment_body = ""
        comment_author = ""
        if latest_comment_url:
            try:
                cr = await client.get(latest_comment_url, headers=self._headers(), timeout=15)
                if cr.status_code == 200:
                    comment_data = cr.json()
                    comment_body = comment_data.get("body", "")
                    comment_author = comment_data.get("user", {}).get("login", "")
            except Exception:
                pass

        watch_tag = cred.watch_tag
        if watch_tag:
            if not comment_body or watch_tag.lower() not in comment_body.lower():
                return

            tag_lower = watch_tag.lower()
            idx = comment_body.lower().find(tag_lower)
            instruction = comment_body[idx + len(watch_tag):].strip() if idx >= 0 else comment_body

            text_parts = [
                f"[{repo_full}] {subject_type}: {subject_title}",
                f"Comment by @{comment_author}: {instruction}",
            ]

            await self._message_callback(PlatformMessage(
                platform=self.spec.platform_id,
                sender_id=comment_author,
                sender_name=comment_author,
                text="\n".join(text_parts),
                channel_id=repo_full,
                channel_name=repo_full,
                message_id=notif.get("id", ""),
                timestamp=datetime.now(timezone.utc),
                raw={
                    "notification": notif,
                    "trigger": "comment_tag",
                    "tag": watch_tag,
                    "instruction": instruction,
                    "comment_body": comment_body,
                    "comment_author": comment_author,
                },
            ))
            logger.info(f"[GITHUB] Tag '{watch_tag}' matched in {repo_full} by @{comment_author}")
            return

        text_parts = [
            f"[{repo_full}] {subject_type}: {subject_title}",
            f"Reason: {reason}",
        ]
        if comment_body:
            text_parts.append(f"Comment by @{comment_author}: {comment_body[:300]}")

        await self._message_callback(PlatformMessage(
            platform=self.spec.platform_id,
            sender_id=comment_author or "",
            sender_name=comment_author or reason,
            text="\n".join(text_parts),
            channel_id=repo_full,
            channel_name=repo_full,
            message_id=notif.get("id", ""),
            timestamp=datetime.now(timezone.utc),
            raw=notif,
        ))

    # ----- REST API methods -----

    async def get_authenticated_user(self) -> Result:
        return await arequest(
            "GET", f"{GITHUB_API}/user",
            headers=self._headers(),
            expected=(200,),
            transform=lambda d: {"login": d.get("login"), "name": d.get("name"), "id": d.get("id")},
        )

    async def list_repos(self, per_page: int = 30, sort: str = "updated") -> Result:
        return await arequest(
            "GET", f"{GITHUB_API}/user/repos",
            headers=self._headers(),
            params={"per_page": per_page, "sort": sort},
            expected=(200,),
            transform=lambda d: {"repos": [
                {"full_name": r.get("full_name"), "name": r.get("name"), "private": r.get("private"), "description": r.get("description", "")}
                for r in d
            ]},
        )

    async def get_repo(self, owner_repo: str) -> Result:
        return await arequest(
            "GET", f"{GITHUB_API}/repos/{owner_repo}",
            headers=self._headers(),
            expected=(200,),
        )

    async def list_issues(self, owner_repo: str, state: str = "open", per_page: int = 30) -> Result:
        return await arequest(
            "GET", f"{GITHUB_API}/repos/{owner_repo}/issues",
            headers=self._headers(),
            params={"state": state, "per_page": per_page},
            expected=(200,),
            transform=lambda d: {"issues": [
                {
                    "number": i.get("number"),
                    "title": i.get("title"),
                    "state": i.get("state"),
                    "user": i.get("user", {}).get("login", ""),
                    "labels": [l.get("name") for l in i.get("labels", [])],
                    "assignees": [a.get("login") for a in i.get("assignees", [])],
                    "created_at": i.get("created_at"),
                    "updated_at": i.get("updated_at"),
                    "is_pr": "pull_request" in i,
                }
                for i in d
            ]},
        )

    async def get_issue(self, owner_repo: str, number: int) -> Result:
        return await arequest(
            "GET", f"{GITHUB_API}/repos/{owner_repo}/issues/{number}",
            headers=self._headers(),
            expected=(200,),
        )

    async def create_issue(self, owner_repo: str, title: str, body: str = "", labels: Optional[List[str]] = None, assignees: Optional[List[str]] = None) -> Result:
        payload: Dict[str, Any] = {"title": title}
        if body:
            payload["body"] = body
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
        return await arequest(
            "POST", f"{GITHUB_API}/repos/{owner_repo}/issues",
            headers=self._headers(),
            json=payload,
            transform=lambda d: {"number": d.get("number"), "html_url": d.get("html_url"), "title": d.get("title")},
        )

    async def create_comment(self, owner_repo: str, number: int, body: str) -> Result:
        return await arequest(
            "POST", f"{GITHUB_API}/repos/{owner_repo}/issues/{number}/comments",
            headers=self._headers(),
            json={"body": body},
            transform=lambda d: {"id": d.get("id"), "html_url": d.get("html_url")},
        )

    async def list_pull_requests(self, owner_repo: str, state: str = "open", per_page: int = 30) -> Result:
        return await arequest(
            "GET", f"{GITHUB_API}/repos/{owner_repo}/pulls",
            headers=self._headers(),
            params={"state": state, "per_page": per_page},
            expected=(200,),
            transform=lambda d: {"pull_requests": [
                {
                    "number": p.get("number"),
                    "title": p.get("title"),
                    "state": p.get("state"),
                    "user": p.get("user", {}).get("login", ""),
                    "head": p.get("head", {}).get("ref", ""),
                    "base": p.get("base", {}).get("ref", ""),
                    "draft": p.get("draft", False),
                    "created_at": p.get("created_at"),
                }
                for p in d
            ]},
        )

    async def search_issues(self, query: str, per_page: int = 20) -> Result:
        return await arequest(
            "GET", f"{GITHUB_API}/search/issues",
            headers=self._headers(),
            params={"q": query, "per_page": per_page},
            timeout=30.0,
            expected=(200,),
            transform=lambda d: {
                "total_count": d.get("total_count", 0),
                "items": [
                    {
                        "number": i.get("number"),
                        "title": i.get("title"),
                        "state": i.get("state"),
                        "repo": i.get("repository_url", "").split("/repos/")[-1] if i.get("repository_url") else "",
                        "user": i.get("user", {}).get("login", ""),
                        "html_url": i.get("html_url"),
                    }
                    for i in d.get("items", [])
                ],
            },
        )

    async def add_labels(self, owner_repo: str, number: int, labels: List[str]) -> Result:
        return await arequest(
            "POST", f"{GITHUB_API}/repos/{owner_repo}/issues/{number}/labels",
            headers=self._headers(),
            json={"labels": labels},
            expected=(200,),
            transform=lambda _d: {"labels_added": labels},
        )

    async def close_issue(self, owner_repo: str, number: int) -> Result:
        return await arequest(
            "PATCH", f"{GITHUB_API}/repos/{owner_repo}/issues/{number}",
            headers=self._headers(),
            json={"state": "closed"},
            expected=(200,),
            transform=lambda _d: {"closed": True, "number": number},
        )
