"""Autorização por filial — Inspeções de Processo."""

from __future__ import annotations

from app.application.security.api_delpi_permissions import (
    INSPECOES_PROCESSO_BRANCH_VIEW_PERMS,
    INSPECOES_PROCESSO_VIEW,
)
from app.interface.http.branch_access_gate import BranchAccessGate

_GATE = BranchAccessGate(
    global_view_perm=INSPECOES_PROCESSO_VIEW,
    branch_view_perms=dict(INSPECOES_PROCESSO_BRANCH_VIEW_PERMS),
    resource_label="inspeções de processo",
)


def branch_view_allowed(branch: str) -> bool:
    return _GATE.branch_view_allowed(branch)


def consolidated_view_allowed() -> bool:
    return _GATE.consolidated_view_allowed()


def branch_access_error(filial: str | None):
    return _GATE.branch_access_error(filial)
