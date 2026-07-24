"""Autorização por filial — Lançamento de Notas Fiscais."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    LANCAMENTO_NOTAS_FISCAIS_BRANCH_VIEW_PERMS,
    LANCAMENTO_NOTAS_FISCAIS_MANAGE,
    LANCAMENTO_NOTAS_FISCAIS_PROCESS,
    LANCAMENTO_NOTAS_FISCAIS_VIEW,
)
from app.core.responses import error_response


def _is_superadmin() -> bool:
    user = get_current_user()
    return bool(user and getattr(user, "is_superadmin", False))


def has_global_branch_access() -> bool:
    """`view` / `process` / `manage` (ou superadmin) operam ambas as filiais."""
    if _is_superadmin():
        return True
    user = get_current_user()
    if user is None:
        return False
    return bool(
        has_permission(user, LANCAMENTO_NOTAS_FISCAIS_VIEW)
        or has_permission(user, LANCAMENTO_NOTAS_FISCAIS_PROCESS)
        or has_permission(user, LANCAMENTO_NOTAS_FISCAIS_MANAGE)
    )


def branch_view_allowed(branch: str) -> bool:
    """True se o usuário pode operar a filial (menu/API).

    Acesso global libera ambas. Caso contrário exige
    `lancamento-notas-fiscais.view.filial-01|02`.
    """
    if has_global_branch_access():
        return True

    user = get_current_user()
    if user is None:
        return False

    branch_perm = LANCAMENTO_NOTAS_FISCAIS_BRANCH_VIEW_PERMS.get(str(branch).strip())
    return branch_perm is not None and has_permission(user, branch_perm)


def branch_access_error(branch: str):
    if branch_view_allowed(branch):
        return None
    return error_response(
        "Sem permissão para acessar solicitações desta filial.",
        status_code=403,
        code="BRANCH_FORBIDDEN",
        recoverable=False,
    )
