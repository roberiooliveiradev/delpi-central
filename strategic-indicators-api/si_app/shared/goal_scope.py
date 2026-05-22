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
    """
    Metas por filial (01/02) para indicadores consolidated e per_unit.

    per_unit mede realizado por unidade; metas distintas por filial usam
    goal_scope_branch, sem precisar duplicar o indicador (ex.: ROL Matriz/Filial).
    """
    return (scope_type or "").strip() in {"consolidated", "per_unit"}


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


def format_goal_scope_label(goal_scope_branch: str | None) -> str:
    branch = normalize_goal_scope_branch(goal_scope_branch)
    if branch in BRANCH_UNIT_CODES:
        return f"Meta filial {format_branch_scope_label(branch)}"
    return "Meta consolidada"


def _format_branch_list_label(branch_codes: list[str]) -> str:
    codes = [
        format_branch_scope_label(code)
        for code in branch_codes
        if normalize_goal_scope_branch(code) in BRANCH_UNIT_CODES
    ]
    if not codes:
        return ""
    if len(codes) == 1:
        return codes[0]
    if len(codes) == 2:
        return f"{codes[0]} e {codes[1]}"
    return ", ".join(codes[:-1]) + f" e {codes[-1]}"


def resolve_goal_scope_hint_for_view(
    *,
    view_branch: str | None,
    consolidated_goal: dict | None,
    branch_goals: dict[str, dict] | None,
) -> str | None:
    """
    Mensagem quando a visão atual não resolve meta, mas outro escopo tem meta ativa.
    """
    view = normalize_goal_scope_branch(view_branch)
    by_branch = branch_goals or {}
    has_consolidated = bool(consolidated_goal and consolidated_goal.get("goal_label"))
    available_branches = [
        code
        for code in BRANCH_UNIT_CODES
        if by_branch.get(code, {}).get("goal_label")
    ]

    if not view:
        if available_branches and not has_consolidated:
            branches = _format_branch_list_label(available_branches)
            if len(available_branches) >= 2:
                return (
                    f"Metas cadastradas apenas por filial ({branches}). "
                    "Selecione uma filial no filtro."
                )
            return (
                f"Meta cadastrada apenas para filial {branches}. "
                f"Selecione a filial {branches} no filtro."
            )
        return None

    if view not in BRANCH_UNIT_CODES:
        return None

    if has_consolidated and view not in available_branches:
        return (
            "Meta cadastrada apenas no consolidado. "
            "Selecione Consolidado no filtro de filial."
        )

    if available_branches and view not in available_branches:
        branches = _format_branch_list_label(available_branches)
        if len(available_branches) == 1:
            return (
                f"Meta cadastrada apenas para filial {branches}. "
                f"Selecione a filial {branches} no filtro."
            )
        return (
            f"Metas cadastradas apenas para filiais {branches}, "
            f"não para filial {format_branch_scope_label(view)}. "
            "Ajuste o filtro de filial."
        )

    return None
