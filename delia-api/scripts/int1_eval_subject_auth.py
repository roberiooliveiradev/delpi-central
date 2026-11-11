"""Eval-only subject access-token lifecycle helpers.

Used by INT-1 harnesses. Never logs raw tokens. Injectable HTTP for
offline tests. Reuses the Portal password-grant gateway path already
approved for eval (same as native_mcptoolset_direct_eval).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SubjectAccessSession:
    """Subject access session metadata (never log the token)."""

    access_token: str
    acquired_at_epoch: float
    expires_at_epoch: float | None
    expires_in_seconds: int | None
    token_fingerprint: str


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def fingerprint_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]


def acquire_subject_access_session(
    *,
    http_post: Callable[[str, Mapping[str, str]], Mapping[str, Any]] | None = None,
    now: float | None = None,
) -> SubjectAccessSession:
    """Mint Portal subject access token via the approved gateway path."""
    token_url = (
        _env("KC_GATEWAY_TOKEN_BASE") or "http://delpi-gateway/auth"
    ).rstrip("/") + "/realms/delpi/protocol/openid-connect/token"
    form = {
        "grant_type": "password",
        "client_id": _env("VITE_KC_CLIENT_ID") or "delpi-central",
        "username": _env("DEV_PORTAL_USERNAME"),
        "password": _env("DEV_PORTAL_PASSWORD"),
        "scope": "openid",
    }
    acquired = float(time.time() if now is None else now)
    if http_post is not None:
        payload = http_post(token_url, form)
    else:
        data = urllib.parse.urlencode(form).encode()
        req = urllib.request.Request(token_url, data=data)
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode())
    token = payload.get("access_token") if isinstance(payload, Mapping) else None
    if not isinstance(token, str) or not token.strip():
        raise RuntimeError("subject_token_empty")
    expires_in = payload.get("expires_in") if isinstance(payload, Mapping) else None
    try:
        expires_in_i = int(expires_in) if expires_in is not None else None
    except (TypeError, ValueError):
        expires_in_i = None
    expires_at = (
        acquired + float(expires_in_i) if expires_in_i is not None else None
    )
    cleaned = token.strip()
    return SubjectAccessSession(
        access_token=cleaned,
        acquired_at_epoch=acquired,
        expires_at_epoch=expires_at,
        expires_in_seconds=expires_in_i,
        token_fingerprint=fingerprint_token(cleaned),
    )


def subject_session_is_fresh(
    session: SubjectAccessSession,
    *,
    now: float | None = None,
    skew_seconds: float = 90.0,
) -> bool:
    if session.expires_at_epoch is None:
        return True
    clock = float(time.time() if now is None else now)
    return session.expires_at_epoch > (clock + float(skew_seconds))


def subject_session_public_meta(session: SubjectAccessSession) -> dict[str, Any]:
    return {
        "auth_acquired_at_epoch": session.acquired_at_epoch,
        "auth_expires_at_epoch": session.expires_at_epoch,
        "auth_expires_in_seconds": session.expires_in_seconds,
        "auth_token_fingerprint": session.token_fingerprint,
    }
