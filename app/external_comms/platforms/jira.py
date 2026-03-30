# -*- coding: utf-8 -*-
"""Jira Cloud REST API client — direct HTTP via httpx.

Supports two auth modes:
- **API Token**: email + API token (Atlassian account).
- **OAuth 2.0**: access_token + cloud_id (from CraftOS backend OAuth flow).

Listening is implemented via polling the Jira search API (JQL) for
recently-updated issues. An optional **watch_labels** filter lets
users restrict events to issues carrying specific labels.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import httpx

from app.external_comms.base import BasePlatformClient, PlatformMessage, MessageCallback
from app.external_comms.credentials import has_credential, load_credential, save_credential, remove_credential
from app.external_comms.registry import register_client

try:
    from app.logger import logger
except Exception:
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

JIRA_CLOUD_API = "https://api.atlassian.com/ex/jira"
CREDENTIAL_FILE = "jira.json"

POLL_INTERVAL = 10      # seconds between polls
RETRY_DELAY = 15        # seconds to wait after a poll error


@dataclass
class JiraCredential:
    # API-token auth
    domain: str = ""            # e.g. "mycompany.atlassian.net"
    email: str = ""
    api_token: str = ""
    # OAuth auth (from CraftOS backend)
    cloud_id: str = ""
    access_token: str = ""
    refresh_token: str = ""
    token_expiry: float = 0.0
    site_url: str = ""
    # Listener settings
    watch_labels: List[str] = field(default_factory=list)
    watch_tag: str = ""  # e.g. "@craftbot" — only trigger on comments containing this tag


@register_client
class JiraClient(BasePlatformClient):
    """Jira Cloud platform client with JQL-based polling listener."""

    PLATFORM_ID = "jira"

    def __init__(self) -> None:
        super().__init__()
        self._cred: Optional[JiraCredential] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._last_poll_time: Optional[str] = None  # ISO 8601
        self._seen_issue_keys: set = set()
        self._catchup_done: bool = False

    # ------------------------------------------------------------------
    # Credential helpers
    # ------------------------------------------------------------------

    def has_credentials(self) -> bool:
        return has_credential(CREDENTIAL_FILE)

    def _load(self) -> JiraCredential:
        if self._cred is None:
            self._cred = load_credential(CREDENTIAL_FILE, JiraCredential)
        if self._cred is None:
            raise RuntimeError("No Jira credentials. Use /jira login first.")
        return self._cred

    def _is_oauth(self) -> bool:
        cred = self._load()
        return bool(cred.cloud_id and cred.access_token)

    def _base_url(self) -> str:
        cred = self._load()
        if cred.cloud_id:
            return f"{JIRA_CLOUD_API}/{cred.cloud_id}/rest/api/3"
        if cred.domain:
            domain = cred.domain.rstrip("/")
            if not domain.startswith("http"):
                domain = f"https://{domain}"
            return f"{domain}/rest/api/3"
        raise RuntimeError("No Jira domain or cloud_id configured.")

    def _headers(self) -> Dict[str, str]:
        cred = self._load()
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if cred.cloud_id and cred.access_token:
            headers["Authorization"] = f"Bearer {cred.access_token}"
        elif cred.email and cred.api_token:
            import base64
            raw = f"{cred.email}:{cred.api_token}"
            encoded = base64.b64encode(raw.encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"
        else:
            raise RuntimeError("Incomplete Jira credentials (need email+api_token or cloud_id+access_token).")
        return headers

    # ------------------------------------------------------------------
    # BasePlatformClient interface
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        self._load()
        self._connected = True

    async def send_message(self, recipient: str, text: str, **kwargs) -> Dict[str, Any]:
        """Send a comment to a Jira issue.

        Args:
            recipient: Issue key (e.g. "PROJ-123").
            text: Comment body text.
        """
        return await self.add_comment(recipient, text)

    # ------------------------------------------------------------------
    # Watch-label configuration
    # ------------------------------------------------------------------

    def get_watch_labels(self) -> List[str]:
        """Return the list of labels the listener filters on."""
        cred = self._load()
        return list(cred.watch_labels)

    def set_watch_labels(self, labels: List[str]) -> None:
        """Set the labels to filter on when listening.

        Pass an empty list to watch all issues (no filtering).
        """
        cred = self._load()
        cred.watch_labels = [lbl.strip() for lbl in labels if lbl.strip()]
        save_credential(CREDENTIAL_FILE, cred)
        self._cred = cred
        logger.info(f"[JIRA] Watch labels set to: {cred.watch_labels or '(all issues)'}")

    def add_watch_label(self, label: str) -> None:
        """Add a single label to the watch list."""
        cred = self._load()
        label = label.strip()
        if label and label not in cred.watch_labels:
            cred.watch_labels.append(label)
            save_credential(CREDENTIAL_FILE, cred)
            self._cred = cred
            logger.info(f"[JIRA] Added watch label: {label}")

    def remove_watch_label(self, label: str) -> None:
        """Remove a single label from the watch list."""
        cred = self._load()
        label = label.strip()
        if label in cred.watch_labels:
            cred.watch_labels.remove(label)
            save_credential(CREDENTIAL_FILE, cred)
            self._cred = cred
            logger.info(f"[JIRA] Removed watch label: {label}")

    # -- Watch tag (comment mention filter) ----------------------------

    def get_watch_tag(self) -> str:
        """Return the tag the listener filters comments on (e.g. '@craftbot')."""
        cred = self._load()
        return cred.watch_tag

    def set_watch_tag(self, tag: str) -> None:
        """Set the mention tag to watch for in comments.

        Only comments containing this tag will trigger events.
        Pass an empty string to trigger on all issue updates (no comment filtering).
        """
        cred = self._load()
        cred.watch_tag = tag.strip()
        save_credential(CREDENTIAL_FILE, cred)
        self._cred = cred
        logger.info(f"[JIRA] Watch tag set to: {cred.watch_tag or '(disabled — all updates)'}")

    # ------------------------------------------------------------------
    # Listening (JQL polling)
    # ------------------------------------------------------------------

    @property
    def supports_listening(self) -> bool:
        return True

    async def start_listening(self, callback: MessageCallback) -> None:
        if self._listening:
            return

        self._message_callback = callback
        self._load()

        # Verify credentials
        me = await self.get_myself()
        if "error" in me:
            raise RuntimeError(f"Invalid Jira credentials: {me.get('error')}")

        display = me.get("result", {}).get("displayName", "unknown")
        logger.info(f"[JIRA] Authenticated as: {display}")

        # Catchup: set last poll time to now
        self._last_poll_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
        self._catchup_done = True
        self._listening = True
        self._poll_task = asyncio.create_task(self._poll_loop())

        cred = self._load()
        labels_info = ", ".join(cred.watch_labels) if cred.watch_labels else "(all)"
        tag_info = cred.watch_tag or "(disabled — all updates)"
        logger.info(f"[JIRA] Poller started — labels: {labels_info} | tag: {tag_info}")

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
        logger.info("[JIRA] Poller stopped")

    async def _poll_loop(self) -> None:
        while self._listening:
            try:
                await self._check_updates()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[JIRA] Poll error: {e}")
                await asyncio.sleep(RETRY_DELAY)
                continue
            await asyncio.sleep(POLL_INTERVAL)

    async def _check_updates(self) -> None:
        if not self._last_poll_time:
            return

        cred = self._load()

        # Build JQL
        jql_parts = [f'updated >= "{self._last_poll_time}"']
        if cred.watch_labels:
            label_clauses = " OR ".join(f'labels = "{lbl}"' for lbl in cred.watch_labels)
            jql_parts.append(f"({label_clauses})")
        jql = " AND ".join(jql_parts)
        jql += " ORDER BY updated ASC"

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url()}/search/jql",
                headers=self._headers(),
                json={
                    "jql": jql,
                    "maxResults": 50,
                    "fields": ["summary", "status", "assignee", "reporter", "labels", "updated", "comment", "issuetype", "priority", "project"],
                },
                timeout=30,
            )

            if resp.status_code == 401:
                logger.warning("[JIRA] Authentication expired (401)")
                return
            if resp.status_code != 200:
                logger.warning(f"[JIRA] Search API error: {resp.status_code} — {resp.text[:300]}")
                return

            data = resp.json()
            issues = data.get("issues", [])

            for issue in issues:
                issue_key = issue.get("key", "")
                updated = issue.get("fields", {}).get("updated", "")

                # Build a dedup key from issue key + updated timestamp
                dedup_key = f"{issue_key}:{updated}"
                if dedup_key in self._seen_issue_keys:
                    continue
                self._seen_issue_keys.add(dedup_key)

                await self._dispatch_issue(issue)

            # Update poll time
            self._last_poll_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

            # Cap seen set
            if len(self._seen_issue_keys) > 500:
                self._seen_issue_keys = set(list(self._seen_issue_keys)[-200:])

    async def _dispatch_issue(self, issue: Dict[str, Any]) -> None:
        if not self._message_callback:
            return

        cred = self._load()
        fields_data = issue.get("fields", {})
        issue_key = issue.get("key", "")
        summary = fields_data.get("summary", "")
        status_name = (fields_data.get("status") or {}).get("name", "")
        issue_type = (fields_data.get("issuetype") or {}).get("name", "")
        priority = (fields_data.get("priority") or {}).get("name", "")
        project_key = (fields_data.get("project") or {}).get("key", "")
        labels = fields_data.get("labels", [])

        assignee = fields_data.get("assignee") or {}
        assignee_name = assignee.get("displayName", "Unassigned")

        reporter = fields_data.get("reporter") or {}
        reporter_name = reporter.get("displayName", "Unknown")

        # Extract comments
        comments = (fields_data.get("comment") or {}).get("comments", [])

        # --- Watch tag filtering ---
        # If a watch_tag is set, only dispatch when a comment contains the tag.
        # The triggering comment text (after the tag) becomes the message.
        watch_tag = cred.watch_tag
        if watch_tag:
            matching_comment = None
            tag_lower = watch_tag.lower()
            # Scan comments newest-first for one containing the tag
            for comment in reversed(comments):
                comment_body = _extract_adf_text(comment.get("body", {}))
                if tag_lower in comment_body.lower():
                    # Dedup: use comment ID so we don't re-trigger on same comment
                    comment_id = comment.get("id", "")
                    comment_dedup = f"{issue_key}:comment:{comment_id}"
                    if comment_dedup in self._seen_issue_keys:
                        continue
                    self._seen_issue_keys.add(comment_dedup)
                    matching_comment = comment
                    break

            if matching_comment is None:
                # No comment with the tag — skip this issue entirely
                return

            # Build message from the tagged comment
            comment_author = (matching_comment.get("author") or {}).get("displayName", "Unknown")
            comment_author_id = (matching_comment.get("author") or {}).get("accountId", "")
            comment_body = _extract_adf_text(matching_comment.get("body", {}))

            # Strip the tag from the comment to get the instruction
            idx = comment_body.lower().find(tag_lower)
            if idx >= 0:
                instruction = comment_body[idx + len(watch_tag):].strip()
            else:
                instruction = comment_body

            text_parts = [
                f"[{issue_key}] {summary}",
                f"Status: {status_name} | Assignee: {assignee_name}",
                f"Comment by {comment_author}: {instruction or comment_body}",
            ]

            timestamp = None
            created_str = matching_comment.get("created", "")
            if created_str:
                try:
                    timestamp = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                except Exception:
                    pass

            platform_msg = PlatformMessage(
                platform="jira",
                sender_id=comment_author_id,
                sender_name=comment_author,
                text="\n".join(text_parts),
                channel_id=project_key,
                channel_name=f"{project_key} ({issue_type})",
                message_id=f"{issue_key}:{matching_comment.get('id', '')}",
                timestamp=timestamp,
                raw={
                    "issue": issue,
                    "trigger": "comment_tag",
                    "tag": watch_tag,
                    "instruction": instruction or comment_body,
                    "comment": matching_comment,
                },
            )

            await self._message_callback(platform_msg)
            logger.info(f"[JIRA] Tag '{watch_tag}' matched in {issue_key} by {comment_author}: {instruction[:80]}...")
            return

        # --- No watch tag — dispatch all updates (original behavior) ---
        text_parts = [
            f"[{issue_key}] {summary}",
            f"Type: {issue_type} | Priority: {priority} | Status: {status_name}",
            f"Project: {project_key} | Assignee: {assignee_name}",
        ]
        if labels:
            text_parts.append(f"Labels: {', '.join(labels)}")

        if comments:
            latest_comment = comments[-1]
            comment_author = (latest_comment.get("author") or {}).get("displayName", "")
            comment_body = _extract_adf_text(latest_comment.get("body", {}))
            if comment_body:
                text_parts.append(f"Latest comment by {comment_author}: {comment_body[:200]}")

        timestamp = None
        updated_str = fields_data.get("updated", "")
        if updated_str:
            try:
                timestamp = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            except Exception:
                pass

        platform_msg = PlatformMessage(
            platform="jira",
            sender_id=reporter.get("accountId", ""),
            sender_name=reporter_name,
            text="\n".join(text_parts),
            channel_id=project_key,
            channel_name=f"{project_key} ({issue_type})",
            message_id=issue_key,
            timestamp=timestamp,
            raw=issue,
        )

        await self._message_callback(platform_msg)

    # ------------------------------------------------------------------
    # Jira REST API methods
    # ------------------------------------------------------------------

    async def get_myself(self) -> Dict[str, Any]:
        """Get the authenticated user's info."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._base_url()}/myself",
                    headers=self._headers(),
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "ok": True,
                        "result": {
                            "accountId": data.get("accountId"),
                            "displayName": data.get("displayName"),
                            "emailAddress": data.get("emailAddress", ""),
                            "active": data.get("active", True),
                        },
                    }
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def search_issues(
        self,
        jql: str,
        max_results: int = 50,
        fields_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search for issues using JQL.

        Args:
            jql: JQL query string.
            max_results: Maximum number of results (max 100).
            fields_list: List of fields to return.

        Returns:
            API response with matching issues or error.
        """
        payload: Dict[str, Any] = {
            "jql": jql,
            "maxResults": min(max_results, 100),
        }
        if fields_list:
            payload["fields"] = fields_list

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._base_url()}/search/jql",
                    headers=self._headers(),
                    json=payload,
                    timeout=30,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "ok": True,
                        "result": {
                            "total": data.get("total", 0),
                            "issues": data.get("issues", []),
                        },
                    }
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def get_issue(
        self,
        issue_key: str,
        fields_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get a single issue by key.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
            fields_list: Optional list of fields to return.

        Returns:
            API response with issue data or error.
        """
        params: Dict[str, Any] = {}
        if fields_list:
            params["fields"] = ",".join(fields_list)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._base_url()}/issue/{issue_key}",
                    headers=self._headers(),
                    params=params,
                    timeout=15,
                )
                if resp.status_code == 200:
                    return {"ok": True, "result": resp.json()}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str = "Task",
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        labels: Optional[List[str]] = None,
        priority: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new issue.

        Args:
            project_key: Project key (e.g. "PROJ").
            summary: Issue summary/title.
            issue_type: Issue type name (e.g. "Task", "Bug", "Story").
            description: Optional plain-text description (converted to ADF).
            assignee_id: Optional Atlassian account ID.
            labels: Optional list of label strings.
            priority: Optional priority name (e.g. "High").
            extra_fields: Optional additional fields dict.

        Returns:
            API response with created issue key/id or error.
        """
        fields_payload: Dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }

        if description:
            fields_payload["description"] = _text_to_adf(description)
        if assignee_id:
            fields_payload["assignee"] = {"accountId": assignee_id}
        if labels:
            fields_payload["labels"] = labels
        if priority:
            fields_payload["priority"] = {"name": priority}
        if extra_fields:
            fields_payload.update(extra_fields)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._base_url()}/issue",
                    headers=self._headers(),
                    json={"fields": fields_payload},
                    timeout=15,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    return {
                        "ok": True,
                        "result": {
                            "id": data.get("id"),
                            "key": data.get("key"),
                            "self": data.get("self"),
                        },
                    }
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def update_issue(
        self,
        issue_key: str,
        fields_update: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update an existing issue's fields.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
            fields_update: Dict of field names to new values.

        Returns:
            API response or error.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.put(
                    f"{self._base_url()}/issue/{issue_key}",
                    headers=self._headers(),
                    json={"fields": fields_update},
                    timeout=15,
                )
                if resp.status_code == 204:
                    return {"ok": True, "result": {"updated": True, "key": issue_key}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def add_comment(
        self,
        issue_key: str,
        body: str,
    ) -> Dict[str, Any]:
        """Add a comment to an issue.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
            body: Comment body text (converted to ADF).

        Returns:
            API response with comment details or error.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._base_url()}/issue/{issue_key}/comment",
                    headers=self._headers(),
                    json={"body": _text_to_adf(body)},
                    timeout=15,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    return {
                        "ok": True,
                        "result": {
                            "id": data.get("id"),
                            "created": data.get("created"),
                            "author": (data.get("author") or {}).get("displayName", ""),
                        },
                    }
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def get_transitions(self, issue_key: str) -> Dict[str, Any]:
        """Get available status transitions for an issue.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").

        Returns:
            API response with list of transitions or error.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._base_url()}/issue/{issue_key}/transitions",
                    headers=self._headers(),
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    transitions = [
                        {
                            "id": t.get("id"),
                            "name": t.get("name"),
                            "to": (t.get("to") or {}).get("name", ""),
                        }
                        for t in data.get("transitions", [])
                    ]
                    return {"ok": True, "result": {"transitions": transitions}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transition an issue to a new status.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
            transition_id: Transition ID (from get_transitions).
            comment: Optional comment to add with the transition.

        Returns:
            API response or error.
        """
        payload: Dict[str, Any] = {
            "transition": {"id": transition_id},
        }
        if comment:
            payload["update"] = {
                "comment": [{"add": {"body": _text_to_adf(comment)}}],
            }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self._base_url()}/issue/{issue_key}/transitions",
                    headers=self._headers(),
                    json=payload,
                    timeout=15,
                )
                if resp.status_code == 204:
                    return {"ok": True, "result": {"transitioned": True, "key": issue_key}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def assign_issue(
        self,
        issue_key: str,
        account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assign an issue to a user (or unassign with None).

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
            account_id: Atlassian account ID, or None to unassign.

        Returns:
            API response or error.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.put(
                    f"{self._base_url()}/issue/{issue_key}/assignee",
                    headers=self._headers(),
                    json={"accountId": account_id},
                    timeout=15,
                )
                if resp.status_code == 204:
                    return {"ok": True, "result": {"assigned": True, "key": issue_key}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def get_projects(self, max_results: int = 50) -> Dict[str, Any]:
        """Get list of accessible projects.

        Args:
            max_results: Maximum number of projects to return.

        Returns:
            API response with projects list or error.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._base_url()}/project/search",
                    headers=self._headers(),
                    params={"maxResults": max_results},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    projects = [
                        {
                            "id": p.get("id"),
                            "key": p.get("key"),
                            "name": p.get("name"),
                            "style": p.get("style", ""),
                        }
                        for p in data.get("values", [])
                    ]
                    return {"ok": True, "result": {"projects": projects}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def search_users(
        self,
        query: str,
        max_results: int = 20,
    ) -> Dict[str, Any]:
        """Search for Jira users.

        Args:
            query: Search string (name or email).
            max_results: Maximum results to return.

        Returns:
            API response with matching users or error.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._base_url()}/user/search",
                    headers=self._headers(),
                    params={"query": query, "maxResults": max_results},
                    timeout=15,
                )
                if resp.status_code == 200:
                    users = [
                        {
                            "accountId": u.get("accountId"),
                            "displayName": u.get("displayName"),
                            "emailAddress": u.get("emailAddress", ""),
                            "active": u.get("active", True),
                        }
                        for u in resp.json()
                    ]
                    return {"ok": True, "result": {"users": users}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def get_issue_comments(
        self,
        issue_key: str,
        max_results: int = 50,
    ) -> Dict[str, Any]:
        """Get comments on an issue.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
            max_results: Maximum comments to return.

        Returns:
            API response with comments or error.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._base_url()}/issue/{issue_key}/comment",
                    headers=self._headers(),
                    params={"maxResults": max_results, "orderBy": "-created"},
                    timeout=15,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    comments = [
                        {
                            "id": c.get("id"),
                            "author": (c.get("author") or {}).get("displayName", ""),
                            "body": _extract_adf_text(c.get("body", {})),
                            "created": c.get("created"),
                            "updated": c.get("updated"),
                        }
                        for c in data.get("comments", [])
                    ]
                    return {"ok": True, "result": {"comments": comments, "total": data.get("total", 0)}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def get_statuses(self, project_key: str) -> Dict[str, Any]:
        """Get all statuses for a project.

        Args:
            project_key: Project key (e.g. "PROJ").

        Returns:
            API response with statuses or error.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._base_url()}/project/{project_key}/statuses",
                    headers=self._headers(),
                    timeout=15,
                )
                if resp.status_code == 200:
                    return {"ok": True, "result": resp.json()}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def add_labels(
        self,
        issue_key: str,
        labels: List[str],
    ) -> Dict[str, Any]:
        """Add labels to an issue (without removing existing ones).

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
            labels: List of label strings to add.

        Returns:
            API response or error.
        """
        update_payload = {
            "update": {
                "labels": [{"add": label} for label in labels],
            },
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.put(
                    f"{self._base_url()}/issue/{issue_key}",
                    headers=self._headers(),
                    json=update_payload,
                    timeout=15,
                )
                if resp.status_code == 204:
                    return {"ok": True, "result": {"labels_added": labels, "key": issue_key}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def remove_labels(
        self,
        issue_key: str,
        labels: List[str],
    ) -> Dict[str, Any]:
        """Remove labels from an issue.

        Args:
            issue_key: Issue key (e.g. "PROJ-123").
            labels: List of label strings to remove.

        Returns:
            API response or error.
        """
        update_payload = {
            "update": {
                "labels": [{"remove": label} for label in labels],
            },
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.put(
                    f"{self._base_url()}/issue/{issue_key}",
                    headers=self._headers(),
                    json=update_payload,
                    timeout=15,
                )
                if resp.status_code == 204:
                    return {"ok": True, "result": {"labels_removed": labels, "key": issue_key}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}


# ------------------------------------------------------------------
# ADF (Atlassian Document Format) helpers
# ------------------------------------------------------------------

def _text_to_adf(text: str) -> Dict[str, Any]:
    """Convert plain text to Atlassian Document Format (ADF)."""
    paragraphs = text.split("\n")
    content = []
    for para in paragraphs:
        content.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": para}] if para else [],
        })
    return {
        "version": 1,
        "type": "doc",
        "content": content,
    }


def _extract_adf_text(adf: Dict[str, Any]) -> str:
    """Extract plain text from an ADF document."""
    if not isinstance(adf, dict):
        return str(adf) if adf else ""

    parts: List[str] = []

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if node.get("type") == "text":
                parts.append(node.get("text", ""))
            for child in node.get("content", []):
                _walk(child)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(adf)
    return " ".join(parts)
