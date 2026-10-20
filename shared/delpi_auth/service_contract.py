"""S2S wire contract shared by callers and verifiers.

The individual service credential travels in its own header so the request
can also carry the end-user Bearer in ``Authorization`` (delegated actor).
``X-Delpi-Caller-App`` remains telemetry metadata only — never identity proof.
"""

from __future__ import annotations

from typing import Any, Mapping

SERVICE_AUTHORIZATION_HEADER = "X-Delpi-Service-Authorization"
_BEARER_PREFIX = "bearer "


def build_service_authorization(service_token: str) -> str:
    token = (service_token or "").strip()
    if not token:
        raise ValueError("service_token must be a non-empty JWT")
    return f"Bearer {token}"


def extract_service_authorization(headers: Mapping[str, Any] | None) -> str | None:
    """Return the raw service JWT, or None when the header is absent.

    Raises ``ValueError`` when the header is present but not a non-empty
    Bearer value — a malformed credential is different from no credential.
    """
    value: str | None = None
    for key, raw in (headers or {}).items():
        if str(key).lower() == SERVICE_AUTHORIZATION_HEADER.lower():
            value = str(raw or "").strip()
            break
    if not value:
        return None
    if not value.lower().startswith(_BEARER_PREFIX):
        raise ValueError("service authorization must use the Bearer scheme")
    token = value[len(_BEARER_PREFIX) :].strip()
    if not token:
        raise ValueError("service authorization Bearer token is empty")
    return token
