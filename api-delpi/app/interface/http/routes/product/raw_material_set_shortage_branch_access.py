"""Autorização por filial — ruptura de MP no conjunto do PA."""

from __future__ import annotations

from app.application.security.api_delpi_permissions import (
    API_DELPI_ACCESS,
    PRODUCTION_CONTROL_ACCESS,
    PRODUCTION_CONTROL_BRANCH_VIEW_PERMS,
)
from app.interface.http.branch_access_gate import BranchAccessGate

_GATE = BranchAccessGate(
    global_view_perm=API_DELPI_ACCESS,
    branch_view_perms=dict(PRODUCTION_CONTROL_BRANCH_VIEW_PERMS),
    resource_label="ruptura de matéria-prima no conjunto",
    extra_global_view_perms=(PRODUCTION_CONTROL_ACCESS,),
)


def branch_access_error(branch: str | None):
    return _GATE.branch_access_error(branch)
