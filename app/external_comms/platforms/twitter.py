# -*- coding: utf-8 -*-
"""Twitter/X REST API v2 client — direct HTTP via httpx with OAuth 1.0a.

Supports posting tweets, reading timelines, searching, managing likes/retweets,
and polling for mentions. An optional **watch_tag** lets users restrict
mention triggers to those containing a specific keyword.
"""


import asyncio
import hashlib
import hmac
import logging
import time
import urllib.parse
import secrets
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

TWITTER_API = "https://api.twitter.com/2"
CREDENTIAL_FILE = "twitter.json"

POLL_INTERVAL = 30      # seconds between mention polls
RETRY_DELAY = 60        # seconds to wait after a poll error


@dataclass
class TwitterCredential:
    api_key: str = ""
    api_secret: str = ""
    access_token: str = ""
    access_token_secret: str = ""
    user_id: str = ""
    username: str = ""
    # Listener settings
    watch_tag: str = ""  # only trigger on mentions containing this


def _oauth1_header(
    method: str,
    url: str,
    params: Dict[str, str],
    api_key: str,
    api_secret: str,
    access_token: str,
    access_token_secret: str,
) -> str:
    """Build an OAuth 1.0a Authorization header."""
    oauth_params = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }

    # Combine all params for signature base
    all_params = {**params, **oauth_params}
    sorted_params = "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
        for k, v in sorted(all_params.items())
    )

    base_string = f"{method.upper()}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(sorted_params, safe='')}"
    signing_key = f"{urllib.parse.quote(api_secret, safe='')}&{urllib.parse.quote(access_token_secret, safe='')}"

    import base64
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()

    oauth_params["oauth_signature"] = signature

    header_parts = ", ".join(
        f'{urllib.parse.quote(k, safe="")}="{urllib.parse.quote(v, safe="")}"'
        for k, v in sorted(oauth_params.items())
    )
    return f"OAuth {header_parts}"


@register_client
class TwitterClient(BasePlatformClient):
    """Twitter/X platform client with mention polling."""

    PLATFORM_ID = "twitter"

    def __init__(self) -> None:
        super().__init__()
        self._cred: Optional[TwitterCredential] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._since_id: Optional[str] = None
        self._seen_ids: set = set()

    # ------------------------------------------------------------------
    # Credential helpers
    # ------------------------------------------------------------------

    def has_credentials(self) -> bool:
        return has_credential(CREDENTIAL_FILE)

    def _load(self) -> TwitterCredential:
        if self._cred is None:
            self._cred = load_credential(CREDENTIAL_FILE, TwitterCredential)
        if self._cred is None:
            raise RuntimeError("No Twitter credentials. Use /twitter login first.")
        return self._cred

    def _auth_header(self, method: str, url: str, params: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        cred = self._load()
        return {
            "Authorization": _oauth1_header(
                method, url, params or {},
                cred.api_key, cred.api_secret,
                cred.access_token, cred.access_token_secret,
            ),
        }

    def _bearer_headers(self) -> Dict[str, str]:
        """Use OAuth 1.0a for all requests since we have user context."""
        cred = self._load()
        return {
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # BasePlatformClient interface
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        self._load()
        self._connected = True

    async def send_message(self, recipient: str, text: str, **kwargs) -> Dict[str, Any]:
        """Post a tweet (recipient is ignored for tweets, or used as reply_to tweet ID)."""
        return await self.post_tweet(text, reply_to=recipient if recipient else None)

    # ------------------------------------------------------------------
    # Watch tag configuration
    # ------------------------------------------------------------------

    def get_watch_tag(self) -> str:
        return self._load().watch_tag

    def set_watch_tag(self, tag: str) -> None:
        cred = self._load()
        cred.watch_tag = tag.strip()
        save_credential(CREDENTIAL_FILE, cred)
        self._cred = cred
        logger.info(f"[TWITTER] Watch tag set to: {cred.watch_tag or '(disabled)'}")

    # ------------------------------------------------------------------
    # Listening (mention polling)
    # ------------------------------------------------------------------

    @property
    def supports_listening(self) -> bool:
        return True

    async def start_listening(self, callback: MessageCallback) -> None:
        if self._listening:
            return

        self._message_callback = callback
        cred = self._load()

        # Verify credentials
        me = await self.get_me()
        if "error" in me:
            raise RuntimeError(f"Invalid Twitter credentials: {me.get('error')}")

        user_data = me.get("result", {})
        username = user_data.get("username", "unknown")
        user_id = user_data.get("id", "")
        logger.info(f"[TWITTER] Authenticated as: @{username}")

        # Save user info
        if cred.username != username or cred.user_id != user_id:
            cred.username = username
            cred.user_id = user_id
            save_credential(CREDENTIAL_FILE, cred)
            self._cred = cred

        self._listening = True
        self._poll_task = asyncio.create_task(self._poll_loop())

        tag_info = cred.watch_tag or "(disabled — all mentions)"
        logger.info(f"[TWITTER] Mention poller started — tag: {tag_info}")

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
        logger.info("[TWITTER] Poller stopped")

    async def _poll_loop(self) -> None:
        # Initial catchup: get latest mention ID without dispatching
        try:
            await self._catchup()
        except Exception as e:
            logger.warning(f"[TWITTER] Catchup error: {e}")

        while self._listening:
            try:
                await self._check_mentions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[TWITTER] Poll error: {e}")
                await asyncio.sleep(RETRY_DELAY)
                continue
            await asyncio.sleep(POLL_INTERVAL)

    async def _catchup(self) -> None:
        """Record the latest mention ID without dispatching."""
        cred = self._load()
        if not cred.user_id:
            return

        url = f"{TWITTER_API}/users/{cred.user_id}/mentions"
        params = {"max_results": "5", "tweet.fields": "created_at,author_id,text"}
        auth = self._auth_header("GET", url, params)

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={**auth}, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                tweets = data.get("data", [])
                if tweets:
                    self._since_id = tweets[0].get("id")
                    for t in tweets:
                        self._seen_ids.add(t.get("id"))
                    logger.info(f"[TWITTER] Catchup complete — since_id: {self._since_id}")

    async def _check_mentions(self) -> None:
        cred = self._load()
        if not cred.user_id:
            return

        url = f"{TWITTER_API}/users/{cred.user_id}/mentions"
        params: Dict[str, str] = {
            "max_results": "20",
            "tweet.fields": "created_at,author_id,text,in_reply_to_user_id,conversation_id",
            "expansions": "author_id",
            "user.fields": "username,name",
        }
        if self._since_id:
            params["since_id"] = self._since_id

        auth = self._auth_header("GET", url, params)

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={**auth}, params=params, timeout=15)

            if resp.status_code == 429:
                logger.warning("[TWITTER] Rate limited, backing off")
                await asyncio.sleep(60)
                return
            if resp.status_code != 200:
                logger.warning(f"[TWITTER] Mentions API error: {resp.status_code} — {resp.text[:200]}")
                return

            data = resp.json()
            tweets = data.get("data", [])
            if not tweets:
                return

            # Build user lookup
            includes = data.get("includes", {})
            users_map = {u["id"]: u for u in includes.get("users", [])}

            # Update since_id to newest
            self._since_id = tweets[0].get("id")

            for tweet in reversed(tweets):  # oldest first
                tweet_id = tweet.get("id", "")
                if tweet_id in self._seen_ids:
                    continue
                self._seen_ids.add(tweet_id)

                await self._dispatch_mention(tweet, users_map)

            # Cap seen set
            if len(self._seen_ids) > 500:
                self._seen_ids = set(list(self._seen_ids)[-200:])

    async def _dispatch_mention(self, tweet: Dict[str, Any], users_map: Dict[str, Any]) -> None:
        if not self._message_callback:
            return

        cred = self._load()
        text = tweet.get("text", "")
        author_id = tweet.get("author_id", "")
        author_info = users_map.get(author_id, {})
        author_username = author_info.get("username", "")
        author_name = author_info.get("name", author_username)

        # Watch tag filtering
        watch_tag = cred.watch_tag
        if watch_tag:
            if watch_tag.lower() not in text.lower():
                return
            # Extract instruction after the tag
            tag_lower = watch_tag.lower()
            idx = text.lower().find(tag_lower)
            instruction = text[idx + len(watch_tag):].strip() if idx >= 0 else text
        else:
            instruction = text

        # Remove @mentions from the start for cleaner instruction
        clean_instruction = instruction
        while clean_instruction.startswith("@"):
            parts = clean_instruction.split(" ", 1)
            clean_instruction = parts[1].strip() if len(parts) > 1 else ""

        timestamp = None
        created_at = tweet.get("created_at", "")
        if created_at:
            try:
                timestamp = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except Exception:
                pass

        platform_msg = PlatformMessage(
            platform="twitter",
            sender_id=author_id,
            sender_name=f"@{author_username}" if author_username else author_name,
            text=f"@{author_username}: {clean_instruction or text}",
            channel_id=tweet.get("conversation_id", ""),
            channel_name="Twitter/X",
            message_id=tweet.get("id", ""),
            timestamp=timestamp,
            raw={
                "tweet": tweet,
                "trigger": "mention" if not watch_tag else "mention_tag",
                "tag": watch_tag,
                "instruction": clean_instruction or text,
                "author_username": author_username,
            },
        )

        await self._message_callback(platform_msg)
        logger.info(f"[TWITTER] Mention from @{author_username}: {(clean_instruction or text)[:80]}...")

    # ------------------------------------------------------------------
    # Twitter API v2 methods
    # ------------------------------------------------------------------

    async def get_me(self) -> Dict[str, Any]:
        """Get the authenticated user's info."""
        url = f"{TWITTER_API}/users/me"
        params = {"user.fields": "id,name,username,description,public_metrics"}
        auth = self._auth_header("GET", url, params)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers={**auth}, params=params, timeout=15)
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    return {"ok": True, "result": data}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def post_tweet(self, text: str, reply_to: Optional[str] = None) -> Dict[str, Any]:
        """Post a tweet."""
        url = f"{TWITTER_API}/tweets"
        payload: Dict[str, Any] = {"text": text}
        if reply_to:
            payload["reply"] = {"in_reply_to_tweet_id": reply_to}

        auth = self._auth_header("POST", url)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers={**auth, "Content-Type": "application/json"}, json=payload, timeout=15)
                if resp.status_code in (200, 201):
                    data = resp.json().get("data", {})
                    return {"ok": True, "result": {"id": data.get("id"), "text": data.get("text")}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def delete_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """Delete a tweet."""
        url = f"{TWITTER_API}/tweets/{tweet_id}"
        auth = self._auth_header("DELETE", url)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.delete(url, headers={**auth}, timeout=15)
                if resp.status_code == 200:
                    return {"ok": True, "result": {"deleted": True}}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def get_user_timeline(self, user_id: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:
        """Get a user's recent tweets."""
        cred = self._load()
        uid = user_id or cred.user_id
        if not uid:
            return {"error": "No user_id available"}

        url = f"{TWITTER_API}/users/{uid}/tweets"
        params = {"max_results": str(max_results), "tweet.fields": "created_at,public_metrics,text"}
        auth = self._auth_header("GET", url, params)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers={**auth}, params=params, timeout=15)
                if resp.status_code == 200:
                    return {"ok": True, "result": resp.json()}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def search_tweets(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search recent tweets."""
        url = f"{TWITTER_API}/tweets/search/recent"
        params = {"query": query, "max_results": str(max_results), "tweet.fields": "created_at,author_id,public_metrics,text", "expansions": "author_id", "user.fields": "username"}
        auth = self._auth_header("GET", url, params)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers={**auth}, params=params, timeout=15)
                if resp.status_code == 200:
                    return {"ok": True, "result": resp.json()}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def like_tweet(self, tweet_id: str) -> Dict[str, Any]:
        """Like a tweet."""
        cred = self._load()
        url = f"{TWITTER_API}/users/{cred.user_id}/likes"
        auth = self._auth_header("POST", url)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers={**auth, "Content-Type": "application/json"}, json={"tweet_id": tweet_id}, timeout=15)
                if resp.status_code == 200:
                    return {"ok": True, "result": resp.json().get("data", {})}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def retweet(self, tweet_id: str) -> Dict[str, Any]:
        """Retweet a tweet."""
        cred = self._load()
        url = f"{TWITTER_API}/users/{cred.user_id}/retweets"
        auth = self._auth_header("POST", url)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers={**auth, "Content-Type": "application/json"}, json={"tweet_id": tweet_id}, timeout=15)
                if resp.status_code == 200:
                    return {"ok": True, "result": resp.json().get("data", {})}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def get_user_by_username(self, username: str) -> Dict[str, Any]:
        """Look up a user by username."""
        url = f"{TWITTER_API}/users/by/username/{username}"
        params = {"user.fields": "id,name,username,description,public_metrics"}
        auth = self._auth_header("GET", url, params)
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers={**auth}, params=params, timeout=15)
                if resp.status_code == 200:
                    return {"ok": True, "result": resp.json().get("data", {})}
                return {"error": f"API error: {resp.status_code}", "details": resp.text}
        except Exception as e:
            return {"error": str(e)}

    async def reply_to_tweet(self, tweet_id: str, text: str) -> Dict[str, Any]:
        """Reply to a tweet."""
        return await self.post_tweet(text, reply_to=tweet_id)
