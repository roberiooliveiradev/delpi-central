"""Escopo — inspeções de processo (reexporta escopo Protheus canônico)."""

from __future__ import annotations

from app.domain.totvs.protheus_branches import (
    BRANCH_SCOPE_TODAS,
    BRANCH_SCOPE_VALUES,
    PROTHEUS_BRANCH_CODES,
    is_all_branches,
    normalize_branch_code,
    normalize_branch_scope,
)

VALID_INSPECOES_PROCESSO_BRANCHES = frozenset(PROTHEUS_BRANCH_CODES)

# Compat: None/vazio/Todas → Todas; 01/02 → código.
normalize_optional_branch = normalize_branch_scope

__all__ = [
    "BRANCH_SCOPE_TODAS",
    "BRANCH_SCOPE_VALUES",
    "VALID_INSPECOES_PROCESSO_BRANCHES",
    "is_all_branches",
    "normalize_branch_code",
    "normalize_branch_scope",
    "normalize_optional_branch",
]
