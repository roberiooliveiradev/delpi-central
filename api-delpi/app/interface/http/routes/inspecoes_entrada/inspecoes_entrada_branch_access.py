"""Autorização por filial — Inspeções de Entrada."""

from __future__ import annotations

from app.application.security.api_delpi_permissions import (
    INSPECOES_ENTRADA_BRANCH_VIEW_PERMS,
    INSPECOES_ENTRADA_VIEW,
)
from app.interface.http.branch_access_gate import BranchAccessGate

_GATE = BranchAccessGate(
    global_view_perm=INSPECOES_ENTRADA_VIEW,
    branch_view_perms=dict(INSPECOES_ENTRADA_BRANCH_VIEW_PERMS),
    resource_label="inspeções de entrada",
)


def branch_view_allowed(branch: str) -> bool:
    return _GATE.branch_view_allowed(branch)


def consolidated_view_allowed() -> bool:
    return _GATE.consolidated_view_allowed()


def branch_access_error(filial: str | None):
    return _GATE.branch_access_error(filial)
