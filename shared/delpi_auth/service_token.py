from __future__ import annotations

import os
from typing import Any, Mapping


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


def headers_have_valid_internal_service_token(
    headers: Mapping[str, Any] | None,
) -> bool:
    """Valida token em mapa de headers (FastAPI, Flask ou httpx).

    Sem import de FastAPI — a imagem do chat Flask não inclui fastapi.
    """
    expected = get_internal_service_token()
    if not expected or not headers:
        return False

    def _get(name: str) -> str:
        for key, value in headers.items():
            if str(key).lower() == name.lower():
                return str(value or "").strip()
        return ""

    header_token = _get("X-Delpi-Service-Token")
    if header_token == expected:
        return True

    authorization = _get("Authorization")
    return authorization in {expected, f"Bearer {expected}"}


def request_has_valid_internal_service_token(request: Any) -> bool:
    """Aceita Starlette/FastAPI Request ou qualquer objeto com `.headers`."""
    headers = getattr(request, "headers", None)
    if headers is None:
        return False
    try:
        return headers_have_valid_internal_service_token(dict(headers))
    except Exception:  # noqa: BLE001 — headers opacos
        return headers_have_valid_internal_service_token(headers)
