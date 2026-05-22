from __future__ import annotations

VALID_GOAL_SCOPE_BRANCHES = frozenset({"", "01", "02"})
BRANCH_UNIT_CODES: tuple[str, ...] = ("01", "02")

DEFAULT_PERIOD_SCORES_REFRESH_BRANCHES: tuple[str | None, ...] = (
    None,
    "01",
    "02",
)


def normalize_goal_scope_branch(branch: str | None) -> str:
    """Escopo da meta: vazio = consolidado; códigos TOTVS = filial."""
    return (branch or "").strip()


def is_branch_unit_scope(branch: str | None) -> bool:
    return normalize_goal_scope_branch(branch) in BRANCH_UNIT_CODES


def format_branch_scope_label(branch_code: str) -> str:
    """Rótulo exibido da filial (apenas o código: 01, 02, …)."""
    return normalize_goal_scope_branch(branch_code)


def indicator_allows_branch_goals(scope_type: str | None) -> bool:
    """Indicadores consolidated podem ter metas por filial; per_unit usa só consolidado."""
    return (scope_type or "").strip() == "consolidated"


def supports_branch_goals_for_scope_type(scope_type: str | None) -> bool:
    """Valor persistido em department_indicators.supports_branch_goals."""
    return indicator_allows_branch_goals(scope_type)


def uses_strict_branch_goal_resolution(view_branch: str | None) -> bool:
    """Visão por filial/unidade: não faz fallback para meta consolidada ('')."""
    return is_branch_unit_scope(view_branch)


def indicator_uses_branch_unit_measurement(
    *,
    indicator_branch_goals: dict | None,
    resolved_goal_scope_branch: str | None,
    view_branch: str | None,
) -> bool:
    """
    Realizado por código de filial (01/02) só quando há metas por unidade
    ou meta resolvida explicitamente para a filial da visão.
    """
    active_branch = normalize_goal_scope_branch(view_branch)
    if active_branch not in BRANCH_UNIT_CODES:
        return False

    if indicator_branch_goals:
        return True

    return normalize_goal_scope_branch(resolved_goal_scope_branch) == active_branch


def missing_goal_label_for_view(view_branch: str | None) -> str:
    branch = normalize_goal_scope_branch(view_branch)
    if branch:
        return f"Sem meta para filial {format_branch_scope_label(branch)}"
    return "Sem meta para esta visão"
