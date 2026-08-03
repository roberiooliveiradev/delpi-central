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
from app.domain.totvs.protheus_branches import (
    is_all_branches,
    normalize_branch_code,
    normalize_branch_scope,
)
from app.interface.http.branch_access_gate import BranchAccessGate

AUDIT_5S_BRANCH_VIEW_PERMS = {
    "01": AUDITORIA_5S_VIEW_FILIAL_01,
    "02": AUDITORIA_5S_VIEW_FILIAL_02,
}

AUDIT_5S_BRANCH_AUDIT_PERMS = {
    "01": AUDITORIA_5S_AUDIT_FILIAL_01,
    "02": AUDITORIA_5S_AUDIT_FILIAL_02,
}

_GATE = BranchAccessGate(
    global_view_perm=API_DELPI_QUALITY_ACCESS,
    branch_view_perms=dict(AUDIT_5S_BRANCH_VIEW_PERMS),
    resource_label="Auditoria 5S",
    extra_global_view_perms=(API_DELPI_ACCESS,),
)


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
    if _GATE.branch_view_allowed(branch_code):
        return True

    user = get_current_user()
    if user is None:
        return False

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
    branch_code: str | None,
    *,
    require_audit: bool = False,
    require_admin: bool = False,
):
    if require_admin or require_audit:
        try:
            concrete = normalize_branch_code(branch_code)
        except ValueError:
            return error_response(
                "branch inválida para Auditoria 5S. Use 01 ou 02.",
                status_code=400,
            )
        if require_admin:
            allowed = branch_admin_allowed(concrete)
            message = "Sem permissão administrativa para esta filial da Auditoria 5S."
        else:
            allowed = branch_audit_allowed(concrete)
            message = "Sem permissão para editar o catálogo desta filial."
        if allowed:
            return None
        return error_response(message, status_code=403)

    # Leitura consolidável (Todas | 01 | 02)
    try:
        scope = normalize_branch_scope(branch_code)
    except ValueError:
        return error_response(
            "branch inválida para Auditoria 5S. Use Todas, 01 ou 02.",
            status_code=400,
        )

    if is_all_branches(scope):
        if all(branch_view_allowed(code) for code in ("01", "02")):
            return None
        return error_response(
            "Sem permissão para acessar Auditoria 5S consolidado (Todas as filiais).",
            status_code=403,
        )

    if branch_view_allowed(scope):
        return None
    return error_response(
        "Sem permissão para acessar o catálogo desta filial.",
        status_code=403,
    )
