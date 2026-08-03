"""Autorização por filial — Acompanhamento de Refugos."""

from __future__ import annotations

from app.application.security.api_delpi_permissions import (
    SCRAP_MONITORING_BRANCH_VIEW_PERMS,
    SCRAP_MONITORING_VIEW,
)
from app.interface.http.branch_access_gate import BranchAccessGate

_GATE = BranchAccessGate(
    global_view_perm=SCRAP_MONITORING_VIEW,
    branch_view_perms=dict(SCRAP_MONITORING_BRANCH_VIEW_PERMS),
    resource_label="refugos",
)


def branch_view_allowed(filial: str) -> bool:
    return _GATE.branch_view_allowed(filial)


def consolidated_view_allowed() -> bool:
    return _GATE.consolidated_view_allowed()


def branch_access_error(filial: str | None):
    return _GATE.branch_access_error(filial)
