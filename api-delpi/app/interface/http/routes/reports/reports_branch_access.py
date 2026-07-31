"""Autorização por filial — Delpi Reports."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    REPORTS_BRANCH_MANAGE_PERMS,
    REPORTS_BRANCH_VIEW_PERMS,
    REPORTS_MANAGE,
    REPORTS_NOTES_MANAGE,
    REPORTS_VIEW,
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

    if has_permission(user, REPORTS_VIEW) or has_permission(user, REPORTS_MANAGE):
        return True

    # notes.manage sozinho não libera filial — precisa view.filial-* (ou view/manage).
    branch_perm = REPORTS_BRANCH_VIEW_PERMS.get(branch)
    return branch_perm is not None and has_permission(user, branch_perm)


def branch_manage_allowed(branch: str) -> bool:
    if _is_superadmin():
        return True

    user = get_current_user()
    if user is None:
        return False

    if has_permission(user, REPORTS_MANAGE):
        return True

    branch_perm = REPORTS_BRANCH_MANAGE_PERMS.get(branch)
    return branch_perm is not None and has_permission(user, branch_perm)


def branch_notes_write_allowed(branch: str) -> bool:
    """Gravar acompanhamento: manage da filial OU notes.manage + view da filial."""
    if branch_manage_allowed(branch):
        return True

    user = get_current_user()
    if user is None:
        return False
    if not has_permission(user, REPORTS_NOTES_MANAGE):
        return False
    return branch_view_allowed(branch)


def branch_access_error(branch: str):
    if branch_view_allowed(branch):
        return None
    return error_response(
        "Sem permissão para acessar relatórios desta filial.",
        status_code=403,
    )


def branch_manage_error(branch: str):
    if branch_manage_allowed(branch):
        return None
    return error_response(
        "Sem permissão para gerenciar relatórios desta filial.",
        status_code=403,
    )


def branch_notes_write_error(branch: str):
    if branch_notes_write_allowed(branch):
        return None
    return error_response(
        "Sem permissão para gravar acompanhamento desta filial.",
        status_code=403,
    )
