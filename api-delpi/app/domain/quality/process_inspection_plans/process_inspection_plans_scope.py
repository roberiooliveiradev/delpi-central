"""Escopo — planos de inspeção de processo (reexporta escopo Protheus)."""

from __future__ import annotations

from app.domain.totvs.protheus_branches import (
    BRANCH_SCOPE_ALL,
    BRANCH_SCOPE_VALUES,
    PROTHEUS_BRANCH_CODES,
    is_all_branches,
    normalize_branch_code,
    normalize_branch_scope,
)

normalize_optional_branch = normalize_branch_scope

__all__ = [
    "BRANCH_SCOPE_ALL",
    "BRANCH_SCOPE_VALUES",
    "PROTHEUS_BRANCH_CODES",
    "is_all_branches",
    "normalize_branch_code",
    "normalize_branch_scope",
    "normalize_optional_branch",
]
