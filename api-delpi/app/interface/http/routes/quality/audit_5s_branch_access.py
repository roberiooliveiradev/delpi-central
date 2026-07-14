"""Autorização por filial — Auditoria 5S."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    API_DELPI_ACCESS,
    API_DELPI_QUALITY_ACCESS,
    AUDIT_5S_BRANCH_ADMIN_PERMS,
    AUDITORIA_5S_AUDIT_FILIAL_01,
    AUDITORIA_5S_AUDIT_FILIAL_02,
    AUDITORIA_5S_VIEW_FILIAL_01,
    AUDITORIA_5S_VIEW_FILIAL_02,
)
from app.core.responses import error_response

AUDIT_5S_BRANCH_VIEW_PERMS = {
    "01": AUDITORIA_5S_VIEW_FILIAL_01,
    "02": AUDITORIA_5S_VIEW_FILIAL_02,
}

AUDIT_5S_BRANCH_AUDIT_PERMS = {
    "01": AUDITORIA_5S_AUDIT_FILIAL_01,
    "02": AUDITORIA_5S_AUDIT_FILIAL_02,
}


def _is_superadmin() -> bool:
    user = get_current_user()
    return bool(user and getattr(user, "is_superadmin", False))


def _has_broad_quality_access() -> bool:
    user = get_current_user()
    if user is None:
        return False
    return has_permission(user, API_DELPI_ACCESS) or has_permission(
        user, API_DELPI_QUALITY_ACCESS
    )


def branch_view_allowed(branch_code: str) -> bool:
    if _is_superadmin() or _has_broad_quality_access():
        return True

    user = get_current_user()
    if user is None:
        return False

    branch_perm = AUDIT_5S_BRANCH_VIEW_PERMS.get(branch_code)
    if branch_perm and has_permission(user, branch_perm):
        return True

    audit_perm = AUDIT_5S_BRANCH_AUDIT_PERMS.get(branch_code)
    return audit_perm is not None and has_permission(user, audit_perm)


def branch_audit_allowed(branch_code: str) -> bool:
    if _is_superadmin() or _has_broad_quality_access():
        return True

    user = get_current_user()
    if user is None:
        return False

    audit_perm = AUDIT_5S_BRANCH_AUDIT_PERMS.get(branch_code)
    return audit_perm is not None and has_permission(user, audit_perm)


def branch_admin_allowed(branch_code: str) -> bool:
    if _is_superadmin() or _has_broad_quality_access():
        return True

    user = get_current_user()
    if user is None:
        return False

    admin_perm = AUDIT_5S_BRANCH_ADMIN_PERMS.get(branch_code)
    return admin_perm is not None and has_permission(user, admin_perm)


def branch_access_error(
    branch_code: str,
    *,
    require_audit: bool = False,
    require_admin: bool = False,
):
    if require_admin:
        allowed = branch_admin_allowed(branch_code)
        message = "Sem permissão administrativa para esta filial da Auditoria 5S."
    elif require_audit:
        allowed = branch_audit_allowed(branch_code)
        message = "Sem permissão para editar o catálogo desta filial."
    else:
        allowed = branch_view_allowed(branch_code)
        message = "Sem permissão para acessar o catálogo desta filial."
    if allowed:
        return None
    return error_response(message, status_code=403)
