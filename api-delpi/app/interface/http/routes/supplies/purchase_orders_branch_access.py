"""Autorização por filial — open purchase orders worklist (Suprimentos)."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    API_DELPI_ACCESS,
    DASHBOARD_SUPPLIES_VIEW,
    SUPPLIES_ACCESS,
)
from app.domain.totvs.protheus_branches import PROTHEUS_BRANCH_CODES
from app.interface.http.branch_access_gate import BranchAccessGate

_GATE = BranchAccessGate(
    global_view_perm=DASHBOARD_SUPPLIES_VIEW,
    branch_view_perms={},
    resource_label="pedidos de compra em aberto",
    extra_global_view_perms=(API_DELPI_ACCESS,),
)

_SUPPLIES_UNITS = {
    "01": "supplies.unit.filial-01",
    "02": "supplies.unit.filial-02",
}
_SURFACE = (SUPPLIES_ACCESS,)


def _canonical_unit_allowed(branch: str) -> bool:
    user = get_current_user()
    unit = _SUPPLIES_UNITS.get(branch)
    if user is None or not unit or not has_permission(user, unit):
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
    """Fail-closed: every requested branch must be allowed. Empty is 422 at the route."""
    for code in branches or []:
        error = branch_access_error(code)
        if error:
            return error
    return None
