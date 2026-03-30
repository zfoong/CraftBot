# -*- coding: utf-8 -*-
"""GitHub REST API client — direct HTTP via httpx.

Supports personal access token (PAT) authentication.
Listening is implemented via polling for notifications and
events on watched repositories. An optional **watch_tag** lets
users restrict triggers to issue/PR comments mentioning a tag
(e.g. ``@craftbot``).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from app.external_comms.base import BasePlatformClient, PlatformMessage, MessageCallback
from app.external_comms.credentials import has_credential, load_credential, save_credential, remove_credential
from app.external_comms.registry import register_client

try:
    from app.logger import logger
except Exception:
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

GITHUB_API = "https://api.github.com"
CREDENTIAL_FILE = "github.json"

POLL_INTERVAL = 15      # seconds between polls
RETRY_DELAY = 30        # seconds to wait after a poll error


@dataclass
class GitHubCredential:
    access_token: str = ""
    username: str = ""
    # Listener settings
    watch_repos: List[str] = field(default_factory=list)   # e.g. ["owner/repo"]
    watch_tag: str = ""  # e.g. "@craftbot" — only trigger on comments containing this


@register_client
class GitHubClient(BasePlatformClient):
    """GitHub platform client with notification polling."""

    PLATFORM_ID = "github"

    def __init__(self) -> None:
        super().__init__()
        self._cred: Optional[GitHubCredential] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._last_modified: Optional[str] = None  # If-Modified-Since header
        self._seen_ids: set = set()
        self._catchup_done: bool = False

    # ------------------------------------------------------------------
    # Credential helpers
    # ------------------------------------------------------------------

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
            "Authorization": f"Bearer {cred.access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    # ------------------------------------------------------------------
    # BasePlatformClient interface
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        self._load()
        self._connected = True

    async def send_message(self, recipient: str, text: str, **kwargs) -> Dict[str, Any]:
        """Create a comment on an issue/PR.

        Args:
            recipient: "{owner}/{repo}#{number}" e.g. "octocat/hello-world#1"
            text: Comment body (markdown).
        """
        try:
            # Parse "owner/repo#number"
            repo_part, number = recipient.rsplit("#", 1)
            return await self.create_comment(repo_part.strip(), int(number), text)
        except (ValueError, IndexError):
            return {"error": f"Invalid recipient format. Use 'owner/repo#number', got: {recipient}"}

    # ------------------------------------------------------------------
    # Watch tag / repos configuration
    # ------------------------------------------------------------------

    def get_watch_tag(self) -> str:
        return self._load().watch_tag

    def set_watch_tag(self, tag: str) -> None:
        cred = self._load()
        cred.watch_tag = tag.strip()
        save_credential(CREDENTIAL_FILE, cred)
        self._cred = cred
        logger.info(f"[GITHUB] Watch tag set to: {cred.watch_tag or '(disabled)'}")

    def get_watch_repos(self) -> List[str]:
        return list(self._load().watch_repos)

    def set_watch_repos(self, repos: List[str]) -> None:
        cred = self._load()
        cred.watch_repos = [r.strip() for r in repos if r.strip()]
        save_credential(CREDENTIAL_FILE, cred)
        self._cred = cred
        logger.info(f"[GITHUB] Watch repos set to: {cred.watch_repos or '(all)'}")

    # ------------------------------------------------------------------
    # Listening (notification polling)
    # ------------------------------------------------------------------

    @property
    def supports_listening(self) -> bool:
        return True

    async def start_listening(self, callback: MessageCallback) -> None:
        if self._listening:
            return

        self._message_callback = callback
        self._load()

        # Verify token
        me = await self.get_authenticated_user()
        if "error" in me:
            raise RuntimeError(f"Invalid GitHub token: {me.get('error')}")

        username = me.get("result", {}).get("login", "unknown")
        logger.info(f"[GITHUB] Authenticated as: {username}")

        # Save username
        cred = self._load()
        if cred.username != username:
            cred.username = username
            save_credential(CREDENTIAL_FILE, cred)
            self._cred = cred

        # Catchup: mark current time so we skip old notifications
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
                return  # No new notifications
            if resp.status_code == 401:
                logger.warning("[GITHUB] Authentication expired (401)")
                return
            if resp.status_code != 200:
                logger.warning(f"[GITHUB] Notifications API error: {resp.status_code}")
                return

            # Update Last-Modified for next poll
            lm = resp.headers.get("Last-Modified")
            if lm:
                self._last_modified = lm

            notifications = resp.json()

            for notif in notifications:
                notif_id = notif.get("id", "")
                if notif_id in self._seen_ids:
                    continue
                self._seen_ids.add(notif_id)

                # Filter by watched repos
                repo_full = notif.get("repository", {}).get("full_name", "")
                if cred.watch_repos and repo_full not in cred.watch_repos:
                    continue

                await self._dispatch_notification(client, notif)

            # Cap seen set
            if len(self._seen_ids) > 500:
                self._seen_ids = set(list(self._seen_ids)[-200:])

    async def _dispatch_notification(self, client: httpx.AsyncClient, notif: Dict[str, Any]) -> None:
        if not self._message_callback:
            return

        cred = self._load()
        reason = notif.get("reason", "")
        subject = notif.get("subject", {})
        subject_type = subject.get("type", "")  # Issue, PullRequest, etc.
        subject_title = subject.get("title", "")
        subject_url = subject.get("url", "")
        repo = notif.get("repository", {})
        repo_full = repo.get("full_name", "")

        # Fetch the latest comment if there's a comment URL
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

        # Watch tag filtering
        watch_tag = cred.watch_tag
        if watch_tag:
            if not comment_body or watch_tag.lower() not in comment_body.lower():
                return  # Skip — no matching tag in comment

            # Extract instruction after the tag
            tag_lower = watch_tag.lower()
            idx = comment_body.lower().find(tag_lower)
            instruction = comment_body[idx + len(watch_tag):].strip() if idx >= 0 else comment_body

            text_parts = [
                f"[{repo_full}] {subject_type}: {subject_title}",
                f"Comment by @{comment_author}: {instruction}",
            ]

            platform_msg = PlatformMessage(
                platform="github",
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
            )

            await self._message_callback(platform_msg)
            logger.info(f"[GITHUB] Tag '{watch_tag}' matched in {repo_full} by @{comment_author}: {instruction[:80]}...")
            return

        # No watch tag — dispatch all notifications
        text_parts = [
            f"[{repo_full}] {subject_type}: {subject_title}",
            f"Reason: {reason}",
        ]
        if comment_body:
            text_parts.append(f"Comment by @{comment_author}: {comment_body[:300]}")

        platform_msg = PlatformMessage(
            platform="github",
            sender_id=comment_author or "",
            sender_name=comment_author or reason,
            text="\n".join(text_parts),
            channel_id=repo_full,
            channel_name=repo_full,
            message_id=notif.get("id", ""),
            timestamp=datetime.now(timezone.utc),
            raw=notif,
        )

        await self._message_callback(platform_msg)

    # ------------------------------------------------------------------
    # GitHub REST API methods
    # ------------------------------------------------------------------

    async def get_authenticated_user(self) -> Dict[str, Any]:
        """Get the authenticated user's info."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{GITHUB_API}/user", headers=self._headers(), timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    return {"ok": True, "result": {"login": data.get("login"), "name": data.get("name"), "id": data.get("id")}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def list_repos(self, per_page: int = 30, sort: str = "updated") -> Dict[str, Any]:
        """List repositories for the authenticated user."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{GITHUB_API}/user/repos",
                    headers=self._headers(),
                    params={"per_page": per_page, "sort": sort},
                    timeout=15,
                )
                if resp.status_code == 200:
                    repos = [{"full_name": r.get("full_name"), "name": r.get("name"), "private": r.get("private"), "description": r.get("description", "")} for r in resp.json()]
                    return {"ok": True, "result": {"repos": repos}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def get_repo(self, owner_repo: str) -> Dict[str, Any]:
        """Get repository info."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{GITHUB_API}/repos/{owner_repo}", headers=self._headers(), timeout=15)
                if resp.status_code == 200:
                    return {"ok": True, "result": resp.json()}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def list_issues(self, owner_repo: str, state: str = "open", per_page: int = 30) -> Dict[str, Any]:
        """List issues for a repository."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{GITHUB_API}/repos/{owner_repo}/issues",
                    headers=self._headers(),
                    params={"state": state, "per_page": per_page},
                    timeout=15,
                )
                if resp.status_code == 200:
                    issues = [
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
                        for i in resp.json()
                    ]
                    return {"ok": True, "result": {"issues": issues}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def get_issue(self, owner_repo: str, number: int) -> Dict[str, Any]:
        """Get a specific issue or PR."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{GITHUB_API}/repos/{owner_repo}/issues/{number}", headers=self._headers(), timeout=15)
                if resp.status_code == 200:
                    return {"ok": True, "result": resp.json()}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def create_issue(self, owner_repo: str, title: str, body: str = "", labels: Optional[List[str]] = None, assignees: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a new issue."""
        payload: Dict[str, Any] = {"title": title}
        if body:
            payload["body"] = body
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{GITHUB_API}/repos/{owner_repo}/issues", headers=self._headers(), json=payload, timeout=15)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    return {"ok": True, "result": {"number": data.get("number"), "html_url": data.get("html_url"), "title": data.get("title")}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def create_comment(self, owner_repo: str, number: int, body: str) -> Dict[str, Any]:
        """Create a comment on an issue or PR."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{GITHUB_API}/repos/{owner_repo}/issues/{number}/comments",
                    headers=self._headers(),
                    json={"body": body},
                    timeout=15,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    return {"ok": True, "result": {"id": data.get("id"), "html_url": data.get("html_url")}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def list_pull_requests(self, owner_repo: str, state: str = "open", per_page: int = 30) -> Dict[str, Any]:
        """List pull requests for a repository."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{GITHUB_API}/repos/{owner_repo}/pulls",
                    headers=self._headers(),
                    params={"state": state, "per_page": per_page},
                    timeout=15,
                )
                if resp.status_code == 200:
                    prs = [
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
                        for p in resp.json()
                    ]
                    return {"ok": True, "result": {"pull_requests": prs}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def search_issues(self, query: str, per_page: int = 20) -> Dict[str, Any]:
        """Search issues and PRs."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{GITHUB_API}/search/issues",
                    headers=self._headers(),
                    params={"q": query, "per_page": per_page},
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    items = [
                        {
                            "number": i.get("number"),
                            "title": i.get("title"),
                            "state": i.get("state"),
                            "repo": i.get("repository_url", "").split("/repos/")[-1] if i.get("repository_url") else "",
                            "user": i.get("user", {}).get("login", ""),
                            "html_url": i.get("html_url"),
                        }
                        for i in data.get("items", [])
                    ]
                    return {"ok": True, "result": {"total_count": data.get("total_count", 0), "items": items}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def add_labels(self, owner_repo: str, number: int, labels: List[str]) -> Dict[str, Any]:
        """Add labels to an issue/PR."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{GITHUB_API}/repos/{owner_repo}/issues/{number}/labels",
                    headers=self._headers(),
                    json={"labels": labels},
                    timeout=15,
                )
                if resp.status_code == 200:
                    return {"ok": True, "result": {"labels_added": labels}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def close_issue(self, owner_repo: str, number: int) -> Dict[str, Any]:
        """Close an issue."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.patch(
                    f"{GITHUB_API}/repos/{owner_repo}/issues/{number}",
                    headers=self._headers(),
                    json={"state": "closed"},
                    timeout=15,
                )
                if resp.status_code == 200:
                    return {"ok": True, "result": {"closed": True, "number": number}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}
