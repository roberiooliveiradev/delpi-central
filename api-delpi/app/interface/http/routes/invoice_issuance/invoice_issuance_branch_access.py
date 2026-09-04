"""Autorização por filial — Emissão de Notas Fiscais."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    INVOICE_ISSUANCE_BRANCH_VIEW_PERMS,
    INVOICE_ISSUANCE_MANAGE,
    INVOICE_ISSUANCE_PROCESS,
    INVOICE_ISSUANCE_VIEW,
    MY_REQUESTS_BRANCH_VIEW_PERMS,
    MY_REQUESTS_INVOICE_PROCESS,
    MY_REQUESTS_MANAGE,
    MY_REQUESTS_VIEW_ALL,
)
from app.core.responses import error_response


def _is_superadmin() -> bool:
    user = get_current_user()
    return bool(user and getattr(user, "is_superadmin", False))


def has_global_branch_access() -> bool:
    if _is_superadmin():
        return True
    user = get_current_user()
    if user is None:
        return False
    return bool(
        has_permission(user, INVOICE_ISSUANCE_VIEW)
        or has_permission(user, INVOICE_ISSUANCE_PROCESS)
        or has_permission(user, INVOICE_ISSUANCE_MANAGE)
        or has_permission(user, MY_REQUESTS_VIEW_ALL)
        or has_permission(user, MY_REQUESTS_INVOICE_PROCESS)
        or has_permission(user, MY_REQUESTS_MANAGE)
    )


def branch_view_allowed(branch: str) -> bool:
    if has_global_branch_access():
        return True
    user = get_current_user()
    if user is None:
        return False
    code = str(branch).strip()
    legacy = INVOICE_ISSUANCE_BRANCH_VIEW_PERMS.get(code)
    if legacy is not None and has_permission(user, legacy):
        return True
    modern = MY_REQUESTS_BRANCH_VIEW_PERMS.get(code)
    return modern is not None and has_permission(user, modern)


def branch_access_error(branch: str):
    if branch_view_allowed(branch):
        return None
    return error_response(
        "Sem permissão para acessar solicitações desta filial.",
        status_code=403,
        code="BRANCH_FORBIDDEN",
        recoverable=False,
    )
