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


def mint_request_headers() -> dict[str, str]:
    """Headers for the gateway password-grant mint.

    ``Host: localhost`` makes Keycloak stamp ``iss`` as the front-channel
    issuer (``http://localhost/auth/realms/delpi``) that delegated
    exchange + MCP resource servers expect — same seam as
    ``c3r_mint_bearer.sh`` / ``parallel_mcp_discovery_ab_eval.py``.
    Override with ``DELIA_EVAL_TOKEN_HOST``; set empty to omit Host.
    """
    host = _env("DELIA_EVAL_TOKEN_HOST")
    if "DELIA_EVAL_TOKEN_HOST" not in os.environ:
        host = "localhost"
    if not host:
        return {}
    return {"Host": host}


def subject_token_issuer(token: str) -> str:
    """Return the ``iss`` claim from a JWT without verifying the signature.

    Eval-only diagnostic helper — never logs the token.
    """
    try:
        payload_b64 = token.split(".")[1]
        pad = "=" * (-len(payload_b64) % 4)
        import base64

        claims = json.loads(
            base64.urlsafe_b64decode(payload_b64 + pad).decode("utf-8")
        )
    except (IndexError, ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return ""
    iss = claims.get("iss") if isinstance(claims, Mapping) else None
    return iss.strip() if isinstance(iss, str) else ""


def assert_subject_issuer_matches_configured(
    *,
    access_token: str,
    configured_issuer: str | None = None,
) -> str:
    """Fail closed when minted ``iss`` diverges from KEYCLOAK_ISSUER.

    Proven root cause of E2E ``catalog_failure:mcp_authentication_failed``
    when the harness overrides ``KEYCLOAK_ISSUER`` to a public host while
    the gateway mint still emits ``http://localhost/auth/realms/delpi``:
    ``exchange_host_header`` follows the configured issuer and the
    delegated credential is rejected (0 capabilities, 3 auth failures).
    """
    token_iss = subject_token_issuer(access_token).rstrip("/")
    configured = (
        configured_issuer
        if configured_issuer is not None
        else _env("KEYCLOAK_ISSUER")
    ).strip().rstrip("/")
    if not token_iss:
        raise RuntimeError("subject_issuer_unreadable")
    if configured and token_iss != configured:
        raise RuntimeError(
            "subject_issuer_mismatch:"
            f"token_iss={token_iss}:configured={configured}"
        )
    return token_iss


def acquire_subject_access_session(
    *,
    http_post: Callable[[str, Mapping[str, str]], Mapping[str, Any]] | None = None,
    now: float | None = None,
    align_issuer: bool = True,
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
        # Match probe / MCP resource challenge vocabulary. Keycloak may
        # expand; requesting only ``openid`` historically diverged from
        # the healthy probe mint in ``parallel_mcp_discovery_ab_eval``.
        "scope": "openid profile email",
    }
    acquired = float(time.time() if now is None else now)
    headers = mint_request_headers()
    if http_post is not None:
        payload = http_post(token_url, form)
    else:
        data = urllib.parse.urlencode(form).encode()
        req = urllib.request.Request(token_url, data=data, headers=headers)
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
    # Offline fixtures may inject opaque strings via http_post — only
    # align when the token has JWT shape (three dotted segments).
    if align_issuer and cleaned.count(".") == 2:
        assert_subject_issuer_matches_configured(access_token=cleaned)
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
