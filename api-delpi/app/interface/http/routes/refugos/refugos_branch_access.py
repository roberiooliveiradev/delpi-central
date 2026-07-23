"""Autorização por filial — Acompanhamento de Refugos."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    SCRAP_MONITORING_BRANCH_VIEW_PERMS,
    SCRAP_MONITORING_VIEW,
)
from app.core.responses import error_response
from app.domain.quality.refugos.refugos_scope import VALID_REFUGOS_BRANCHES


def _is_superadmin() -> bool:
    user = get_current_user()
    return bool(user and getattr(user, "is_superadmin", False))


def branch_view_allowed(filial: str) -> bool:
    if _is_superadmin():
        return True

    user = get_current_user()
    if user is None:
        return False

    if has_permission(user, SCRAP_MONITORING_VIEW):
        return True

    branch_perm = SCRAP_MONITORING_BRANCH_VIEW_PERMS.get(filial)
    return branch_perm is not None and has_permission(user, branch_perm)


def consolidated_view_allowed() -> bool:
    return all(branch_view_allowed(branch) for branch in sorted(VALID_REFUGOS_BRANCHES))


def branch_access_error(filial: str | None):
    normalized = str(filial or "").strip() or None
    if normalized is None:
        if consolidated_view_allowed():
            return None
        return error_response(
            "Sem permissão para acessar refugos consolidado (todas as filiais).",
            status_code=403,
        )
    if branch_view_allowed(normalized):
        return None
    return error_response(
        "Sem permissão para acessar refugos desta filial.",
        status_code=403,
    )
