"""Portal Suprimentos context on purchase-requests-api.

Standalone RBAC never reads supplies.access. Global SC accompaniment is
active only for an authenticated request that also proves it came from
supplies-api with a valid internal service token.
"""

from __future__ import annotations

from contextvars import ContextVar

from delpi_auth.service_token import request_has_valid_internal_service_token

from purchase_requests_app.application.security.purchase_requests_permissions import (
    normalize_branch,
)

SUPPLIES_BFF_CALLER = "supplies-api"
_current_request: ContextVar = ContextVar("purchase_requests_http_request", default=None)


def bind_http_request(request):
    return _current_request.set(request)


def reset_http_request(token) -> None:
    _current_request.reset(token)


def _caller_header(request) -> str:
    headers = getattr(request, "headers", None) or {}
    for key, value in headers.items():
        if str(key).lower() == "x-delpi-caller-app":
            return str(value or "").strip()
    return ""


def is_trusted_supplies_bff_call() -> bool:
    request = _current_request.get()
    if request is None:
        return False
    if _caller_header(request) != SUPPLIES_BFF_CALLER:
        return False
    return request_has_valid_internal_service_token(request)


def authorize_portal_branches(branches: list[str]) -> list[str]:
    """Product data scope 01/02. Unknown branch is a contract error, not a grant."""
    if not branches:
        raise ValueError("Filial obrigatória.")
    codes: list[str] = []
    seen: set[str] = set()
    for raw in branches:
        code = normalize_branch(raw)
        if not code:
            raise ValueError("Filial inválida.")
        if code not in seen:
            seen.add(code)
            codes.append(code)
    return codes
