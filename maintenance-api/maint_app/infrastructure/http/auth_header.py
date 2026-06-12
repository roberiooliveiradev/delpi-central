from __future__ import annotations

from delpi_auth.request_context import get_current_user, get_request_authorization
from delpi_auth.service_token import internal_service_authorization


def _normalize_bearer(raw: str) -> str:
    value = raw.strip()
    return value if value.startswith("Bearer ") else f"Bearer {value}"


def bearer_authorization_from_context() -> str | None:
    header_auth = get_request_authorization()
    if header_auth:
        return header_auth

    user = get_current_user()
    if user is not None:
        token = getattr(user, "access_token", None)
        if token:
            return _normalize_bearer(token)

    internal = internal_service_authorization()
    if internal:
        return internal

    return None
