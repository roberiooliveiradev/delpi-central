"""Autorização por filial — análise de estoque de segurança (Suprimentos)."""

from __future__ import annotations

from app.application.security.api_delpi_permissions import (
    SAFETY_STOCK_ACCESS,
    SAFETY_STOCK_BRANCH_VIEW_PERMS,
)
from app.domain.totvs.protheus_branches import PROTHEUS_BRANCH_CODES
from app.interface.http.branch_access_gate import BranchAccessGate

_GATE = BranchAccessGate(
    global_view_perm=SAFETY_STOCK_ACCESS,
    branch_view_perms=dict(SAFETY_STOCK_BRANCH_VIEW_PERMS),
    resource_label="estoque de segurança",
)


def branch_view_allowed(branch: str) -> bool:
    return _GATE.branch_view_allowed(branch)


def list_viewable_branches() -> list[str]:
    return [code for code in PROTHEUS_BRANCH_CODES if branch_view_allowed(code)]


def branch_access_error(branch: str | None):
    return _GATE.branch_access_error(branch)
