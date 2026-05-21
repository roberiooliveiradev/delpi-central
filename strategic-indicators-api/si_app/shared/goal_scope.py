from __future__ import annotations

VALID_GOAL_SCOPE_BRANCHES = frozenset({"", "01", "02"})
BRANCH_UNIT_CODES: tuple[str, ...] = ("01", "02")


def normalize_goal_scope_branch(branch: str | None) -> str:
    """Escopo da meta: vazio = consolidado; códigos TOTVS = filial."""
    return (branch or "").strip()


def format_branch_scope_label(branch_code: str) -> str:
    """Rótulo exibido da filial (apenas o código: 01, 02, …)."""
    return normalize_goal_scope_branch(branch_code)


def indicator_allows_branch_goals(scope_type: str | None) -> bool:
    """Indicadores consolidated podem ter metas por filial; per_unit usa só consolidado."""
    return (scope_type or "").strip() == "consolidated"


def supports_branch_goals_for_scope_type(scope_type: str | None) -> bool:
    """Valor persistido em department_indicators.supports_branch_goals."""
    return indicator_allows_branch_goals(scope_type)
