"""Autorização por filial — Controle de Retrabalhos (padrão inspeções/agendamento)."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    CONTROLE_RETRABALHO_BRANCH_VIEW_PERMS,
    CONTROLE_RETRABALHO_VIEW,
)
from app.core.responses import error_response


def _is_superadmin() -> bool:
    user = get_current_user()
    return bool(user and getattr(user, "is_superadmin", False))


def branch_view_allowed(filial: str) -> bool:
    if _is_superadmin():
        return True

    user = get_current_user()
    if user is None:
        return False

    if has_permission(user, CONTROLE_RETRABALHO_VIEW):
        return True

    branch_perm = CONTROLE_RETRABALHO_BRANCH_VIEW_PERMS.get(filial)
    return branch_perm is not None and has_permission(user, branch_perm)


def branch_access_error(filial: str):
    if branch_view_allowed(filial):
        return None
    return error_response(
        "Sem permissão para acessar retrabalhos desta filial.",
        status_code=403,
    )
