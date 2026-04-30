"""Thin wrappers around httpx for the standard REST envelope.

Most integration clients in this package call REST APIs and translate the
response into the package's ``{ok: True, result: ...}`` / ``{error: ..., details: ...}``
envelope. ``request`` (sync) and ``arequest`` (async) handle the full pattern:

  - send the HTTP request via httpx
  - on a successful status code → wrap the parsed body via ``transform`` (or pass it through)
  - on any other status → return ``{error: "API error: <code>", details: <body text>}``
  - on any exception → return ``{error: str(e)}``

Usage in an integration::

    from ..helpers.http import request

    def get_user(self, user_id: str):
        return request("GET", f"{API_BASE}/users/{user_id}", headers=self._headers())

    def list_users(self, limit: int = 100):
        return request(
            "GET", f"{API_BASE}/users",
            headers=self._headers(),
            params={"limit": limit},
            transform=lambda data: {"users": data, "count": len(data)},
        )
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Optional

import httpx

from .result import Result

_DEFAULT_EXPECTED = (200, 201)


def _shape(r: httpx.Response, expected: Iterable[int],
           transform: Optional[Callable[[Any], Any]]) -> Result:
    if r.status_code in expected:
        try:
            data = r.json()
        except Exception:
            data = None
        if transform is not None:
            return {"ok": True, "result": transform(data)}
        return {"ok": True, "result": data if data is not None else {}}
    return {"error": f"API error: {r.status_code}", "details": r.text}


def request(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    json: Any = None,
    params: Optional[Dict[str, Any]] = None,
    data: Any = None,
    files: Any = None,
    expected: Iterable[int] = _DEFAULT_EXPECTED,
    transform: Optional[Callable[[Any], Any]] = None,
    timeout: float = 15.0,
) -> Result:
    """Sync REST helper. Returns ``{ok, result}`` or ``{error, details}``."""
    try:
        r = httpx.request(
            method, url,
            headers=headers, json=json, params=params,
            data=data, files=files, timeout=timeout,
        )
        return _shape(r, expected, transform)
    except Exception as e:
        return {"error": str(e)}


async def arequest(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    json: Any = None,
    params: Optional[Dict[str, Any]] = None,
    data: Any = None,
    files: Any = None,
    expected: Iterable[int] = _DEFAULT_EXPECTED,
    transform: Optional[Callable[[Any], Any]] = None,
    timeout: float = 15.0,
) -> Result:
    """Async REST helper. Returns ``{ok, result}`` or ``{error, details}``."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.request(
                method, url,
                headers=headers, json=json, params=params,
                data=data, files=files,
            )
        return _shape(r, expected, transform)
    except Exception as e:
        return {"error": str(e)}
