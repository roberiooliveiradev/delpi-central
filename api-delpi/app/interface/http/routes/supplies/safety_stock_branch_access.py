"""Autorização por filial — análise de estoque de segurança (Suprimentos)."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    SAFETY_STOCK_ACCESS,
    SAFETY_STOCK_BRANCH_VIEW_PERMS,
)
from app.core.responses import error_response

_VALID_BRANCHES = ("01", "02")


def _is_superadmin() -> bool:
    user = get_current_user()
    return bool(user and getattr(user, "is_superadmin", False))


def branch_view_allowed(branch: str) -> bool:
    if _is_superadmin():
        return True

    user = get_current_user()
    if user is None:
        return False

    if has_permission(user, SAFETY_STOCK_ACCESS):
        return True

    branch_perm = SAFETY_STOCK_BRANCH_VIEW_PERMS.get(branch)
    return branch_perm is not None and has_permission(user, branch_perm)


def list_viewable_branches() -> list[str]:
    return [branch for branch in _VALID_BRANCHES if branch_view_allowed(branch)]


def branch_access_error(branch: str):
    if branch_view_allowed(branch):
        return None
    return error_response(
        "Sem permissão para acessar estoque de segurança desta filial.",
        status_code=403,
    )
