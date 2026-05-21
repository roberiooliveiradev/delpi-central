from __future__ import annotations

import os

from fastapi import Request


def get_internal_service_token() -> str | None:
    """Token compartilhado entre APIs DELPI (server-to-server)."""
    token = (os.getenv("API_DELPI_INTERNAL_SERVICE_TOKEN") or "").strip()
    return token or None


def internal_service_authorization() -> str | None:
    token = get_internal_service_token()
    if not token:
        return None
    return token if token.startswith("Bearer ") else f"Bearer {token}"


def apply_internal_service_headers(headers: dict[str, str]) -> None:
    token = get_internal_service_token()
    if not token:
        return
    headers["X-Delpi-Service-Token"] = token
    if "Authorization" not in headers:
        auth = internal_service_authorization()
        if auth:
            headers["Authorization"] = auth


def request_has_valid_internal_service_token(request: Request) -> bool:
    expected = get_internal_service_token()
    if not expected:
        return False

    header_token = (request.headers.get("X-Delpi-Service-Token") or "").strip()
    if header_token == expected:
        return True

    authorization = (request.headers.get("Authorization") or "").strip()
    return authorization in {expected, f"Bearer {expected}"}
