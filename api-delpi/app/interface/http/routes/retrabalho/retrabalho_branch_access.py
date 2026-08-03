"""Autorização por filial — Controle de Retrabalhos."""

from __future__ import annotations

from app.application.security.api_delpi_permissions import (
    CONTROLE_RETRABALHO_BRANCH_VIEW_PERMS,
    CONTROLE_RETRABALHO_VIEW,
)
from app.interface.http.branch_access_gate import BranchAccessGate

_GATE = BranchAccessGate(
    global_view_perm=CONTROLE_RETRABALHO_VIEW,
    branch_view_perms=dict(CONTROLE_RETRABALHO_BRANCH_VIEW_PERMS),
    resource_label="retrabalhos",
)


def branch_view_allowed(filial: str) -> bool:
    return _GATE.branch_view_allowed(filial)


def consolidated_view_allowed() -> bool:
    return _GATE.consolidated_view_allowed()


def branch_access_error(filial: str | None):
    return _GATE.branch_access_error(filial)
