"""Canonical authorization fingerprint for cache keys.

Single source for the principal digest used by TV data caches. The
fingerprint separates cache identities only across authorization
contexts (identity, effective permissions, superadmin flag, service
context); it never authorizes and never serializes raw credentials —
when no stable identity claim exists, an opaque credential digest is
used instead.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _user_identity(user: Any) -> str:
    for attribute in ("sub", "id", "user_id", "email", "username"):
        value = getattr(user, attribute, None)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def _user_permissions(user: Any) -> list[str]:
    raw = getattr(user, "permissions", None) or []
    return sorted(
        {str(permission).strip() for permission in raw if str(permission).strip()}
    )


def build_authorization_fingerprint(
    *,
    authorization: str | None,
    user: Any | None = None,
    service_context: str | None = None,
) -> str:
    identity = _user_identity(user)
    principal = {
        "kind": "user" if authorization or user is not None else "service",
        "identity": identity,
        "permissions": _user_permissions(user),
        "isSuperadmin": bool(getattr(user, "is_superadmin", False)),
        "serviceContext": str(service_context or "tv-dashboard").strip(),
        # Fallback opaco quando o modelo HTTP não expõe subject; nunca serializa o token.
        "credentialDigest": hashlib.sha256(authorization.encode("utf-8")).hexdigest()
        if authorization and not identity
        else "",
    }
    return hashlib.sha256(
        json.dumps(principal, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
