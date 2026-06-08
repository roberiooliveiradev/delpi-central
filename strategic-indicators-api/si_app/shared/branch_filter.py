from __future__ import annotations

FINANCIAL_CONSOLIDATED_BRANCH_KEY = "consolidated"

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
    Departamentos com IDD consolidado: medição única (chave consolidated).

    A visão filial no painel repete o mesmo valor via calculador/API; não
    duplicar 01/02 em unit_values para evitar rótulo "02:" no realizado.
    """
    _ = view_branch
    return {"consolidated": consolidated_value}


def consolidated_measurement_value(
    *,
    value: float | None,
    unit_values: dict[str, float | None] | None,
) -> float | None:
    if unit_values and unit_values.get("consolidated") is not None:
        return float(unit_values["consolidated"])
    return value
