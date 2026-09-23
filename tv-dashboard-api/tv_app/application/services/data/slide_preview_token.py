"""Signed opaque tokens for VISTA slide preview PNG URLs (short TTL)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from tv_app.config import settings

DEFAULT_TTL_SEC = 300


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _signing_key() -> bytes:
    secret = (settings.JWT_SECRET or "").strip() or "tv-dashboard-slide-preview"
    return hashlib.sha256(f"tv-vista-slide-preview:{secret}".encode("utf-8")).digest()


def mint_slide_preview_token(
    *,
    playlist_id: str,
    slide_id: str,
    revision: int | str | None,
    ttl_sec: int = DEFAULT_TTL_SEC,
    cache_key: str | None = None,
) -> tuple[str, int]:
    """Return (token, expires_at_unix)."""
    exp = int(time.time()) + max(30, int(ttl_sec))
    payload = {
        "p": str(playlist_id),
        "s": str(slide_id),
        "r": str(revision if revision is not None else ""),
        "e": exp,
    }
    if cache_key:
        payload["k"] = str(cache_key)
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    mac = _b64(hmac.new(_signing_key(), body.encode("ascii"), hashlib.sha256).digest())
    return f"{body}.{mac}", exp


def parse_slide_preview_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    if not raw or "." not in raw or len(raw) < 16:
        raise ValueError("invalid_preview_token")
    left, right = raw.split(".", 1)
    expected = hmac.new(_signing_key(), left.encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _unb64(right)):
        raise ValueError("invalid_preview_token")
    try:
        payload = json.loads(_unb64(left).decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ValueError("invalid_preview_token") from exc
    if not isinstance(payload, dict):
        raise ValueError("invalid_preview_token")
    exp = int(payload.get("e") or 0)
    if exp < int(time.time()):
        raise ValueError("preview_token_expired")
    playlist_id = str(payload.get("p") or "").strip()
    slide_id = str(payload.get("s") or "").strip()
    if not playlist_id or not slide_id:
        raise ValueError("invalid_preview_token")
    parsed = {
        "playlistId": playlist_id,
        "slideId": slide_id,
        "revision": str(payload.get("r") or ""),
        "expiresAt": exp,
    }
    cache_key = str(payload.get("k") or "").strip()
    if cache_key:
        parsed["cacheKey"] = cache_key
    return parsed
