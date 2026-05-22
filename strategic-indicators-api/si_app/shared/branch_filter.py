from __future__ import annotations

CONSOLIDATED_BRANCH_TOKENS = frozenset(
    {
        "",
        "consolidated",
        "consolidated-all",
        "all",
    }
)


def effective_query_branch(branch: str | None) -> str | None:
    """
    Filial efetiva para consultas TOTVS/planilhas.

    Tokens de visão consolidada não devem filtrar colunas de filial (01/02).
    """
    normalized = (branch or "").strip()
    if normalized.lower() in CONSOLIDATED_BRANCH_TOKENS:
        return None
    return normalized


CONSOLIDATED_AGGREGATION_DEPARTMENT_IDS = frozenset(
    {
        "commercial",
        "engineering",
        "financial",
    }
)


def is_consolidated_aggregation_department(department_id: str | None) -> bool:
    return (department_id or "").strip() in CONSOLIDATED_AGGREGATION_DEPARTMENT_IDS


def build_unit_values_for_consolidated_department(
    *,
    consolidated_value: float | None,
    view_branch: str | None = None,
) -> dict[str, float | None]:
    """
    Departamentos com IDD consolidado: visão filial repete o mesmo realizado.
    """
    unit_values: dict[str, float | None] = {"consolidated": consolidated_value}
    effective_branch = effective_query_branch(view_branch)
    if effective_branch is not None:
        unit_values[effective_branch] = consolidated_value
    return unit_values


def consolidated_measurement_value(
    *,
    value: float | None,
    unit_values: dict[str, float | None] | None,
) -> float | None:
    if unit_values and unit_values.get("consolidated") is not None:
        return float(unit_values["consolidated"])
    return value
