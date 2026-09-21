"""Autorização por filial — purchase request lines (Suprimentos).

Direct callers use purchase-requests.* . The purchase-requests-api hop is
trusted only with caller + service token. supplies.access on the user token
is not a branch grant.
"""

from __future__ import annotations

from app.application.security.api_delpi_permissions import (
    PURCHASE_REQUESTS_ACCESS,
    PURCHASE_REQUESTS_BRANCH_VIEW_PERMS,
)
from app.domain.totvs.protheus_branches import PROTHEUS_BRANCH_CODES
from app.interface.http.branch_access_gate import BranchAccessGate
from app.interface.http.supplies_bff_service_access import (
    PURCHASE_REQUESTS_API_CALLER,
    is_trusted_internal_caller,
)

_GATE = BranchAccessGate(
    global_view_perm=PURCHASE_REQUESTS_ACCESS,
    branch_view_perms=dict(PURCHASE_REQUESTS_BRANCH_VIEW_PERMS),
    resource_label="solicitações de compra",
)


def branch_view_allowed(branch: str) -> bool:
    return _GATE.branch_view_allowed(branch)


def list_viewable_branches() -> list[str]:
    return [code for code in PROTHEUS_BRANCH_CODES if branch_view_allowed(code)]


def branch_access_error(branch: str | None):
    if is_trusted_internal_caller(PURCHASE_REQUESTS_API_CALLER):
        return None
    return _GATE.branch_access_error(branch)


def branches_access_error(branches: list[str] | None):
    for code in branches or []:
        error = branch_access_error(code)
        if error:
            return error
    return None
