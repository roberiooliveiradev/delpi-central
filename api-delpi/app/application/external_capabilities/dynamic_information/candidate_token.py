"""Opaque candidate tokens for governed discovery → execution."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


class CandidateTokenError(ValueError):
    """Invalid, expired, or forged candidate token."""


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def mint_candidate_token(
    *,
    action_id: str,
    actor_id: str | None,
    secret: str,
    ttl_seconds: int,
    now: float | None = None,
) -> str:
    if not secret:
        raise CandidateTokenError("Candidate token secret is not configured")
    actor = (actor_id or "").strip()
    if not actor:
        raise CandidateTokenError("actor_id is required")
    ts = int(now if now is not None else time.time())
    payload = {
        "v": 1,
        "action_id": action_id,
        "actor_id": actor,
        "iat": ts,
        "exp": ts + max(1, int(ttl_seconds)),
    }
    body = _b64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    sig = _b64url(
        hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    )
    return f"{body}.{sig}"


def parse_candidate_token(
    token: str,
    *,
    secret: str,
    expected_actor_id: str | None,
    now: float | None = None,
) -> dict[str, Any]:
    if not secret:
        raise CandidateTokenError("Candidate token secret is not configured")
    expected_actor = (expected_actor_id or "").strip()
    if not expected_actor:
        raise CandidateTokenError("actor_id is required")
    if not token or "." not in token:
        raise CandidateTokenError("Malformed candidate token")
    body, sig = token.rsplit(".", 1)
    expected = _b64url(
        hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(expected, sig):
        raise CandidateTokenError("Invalid candidate token signature")
    try:
        payload = json.loads(_b64url_decode(body).decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise CandidateTokenError("Malformed candidate token payload") from exc
    if not isinstance(payload, dict):
        raise CandidateTokenError("Malformed candidate token payload")
    exp = int(payload.get("exp") or 0)
    ts = int(now if now is not None else time.time())
    if exp < ts:
        raise CandidateTokenError("Candidate token expired")
    token_actor = str(payload.get("actor_id") or "").strip()
    if not token_actor:
        raise CandidateTokenError("Candidate token missing actor_id")
    if token_actor != expected_actor:
        raise CandidateTokenError("Candidate token actor mismatch")
    action_id = str(payload.get("action_id") or "").strip()
    if not action_id:
        raise CandidateTokenError("Candidate token missing action_id")
    return payload
