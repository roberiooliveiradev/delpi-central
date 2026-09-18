"""Autorização por filial — purchase request lines (Suprimentos)."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    PURCHASE_REQUESTS_ACCESS,
    PURCHASE_REQUESTS_BRANCH_VIEW_PERMS,
    SUPPLIES_ACCESS,
)
from app.domain.totvs.protheus_branches import PROTHEUS_BRANCH_CODES
from app.interface.http.branch_access_gate import BranchAccessGate

_GATE = BranchAccessGate(
    global_view_perm=PURCHASE_REQUESTS_ACCESS,
    branch_view_perms=dict(PURCHASE_REQUESTS_BRANCH_VIEW_PERMS),
    resource_label="solicitações de compra",
)

_OPERATIONAL_UNITS = frozenset({"01", "02"})
_SURFACE = (SUPPLIES_ACCESS,)


def _canonical_unit_allowed(branch: str) -> bool:
    user = get_current_user()
    if user is None or branch not in _OPERATIONAL_UNITS:
        return False
    return any(has_permission(user, code) for code in _SURFACE)


def branch_view_allowed(branch: str) -> bool:
    if _GATE.branch_view_allowed(branch):
        return True
    return _canonical_unit_allowed(branch)


def list_viewable_branches() -> list[str]:
    return [code for code in PROTHEUS_BRANCH_CODES if branch_view_allowed(code)]


def branch_access_error(branch: str | None):
    return _GATE.branch_access_error(branch)


def branches_access_error(branches: list[str] | None):
    for code in branches or []:
        error = branch_access_error(code)
        if error:
            return error
    return None
