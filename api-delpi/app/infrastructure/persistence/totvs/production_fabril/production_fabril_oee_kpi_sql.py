"""KPI OEE agregado — mesma eficiência canônica da eficiência fabril (HY_TEMPAD × qtd)."""

from __future__ import annotations

from app.domain.production.production_fabril_appointment_scope import (
    DEFAULT_PRODUCTION_BRANCHES,
    EFICIENCIA_FABRIL_VIEW,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_efficiency_sql import (
    FABRIL_EFICIENCIA_PERCENTUAL_SQL,
    FABRIL_KPI_EFFICIENCY_ALIAS,
    fabril_kpi_efficiency_in_valid_range_sql,
)
from app.infrastructure.persistence.totvs.production_fabril.production_fabril_standard_time_sql import (
    FABRIL_STANDARD_TIME_JOINS,
    build_fabril_standard_time_ranked_ctes,
)

OEE_FABRIL_KPI_FROM = f"""
FROM {EFICIENCIA_FABRIL_VIEW} EF WITH (NOLOCK)
{FABRIL_STANDARD_TIME_JOINS}
"""


def _build_oee_kpi_base(
    *,
    where_clause: str,
    where_params: tuple,
    branch: str | None,
    branches: tuple[str, ...],
) -> tuple[str, tuple, str]:
    """WITH SHY/SG2 + subquery de % recalculado; retorna (cte_sql, params, from_calc)."""
    std_cte, std_params = build_fabril_standard_time_ranked_ctes(
        branch=branch,
        branches=branches,
    )
    calc_sql = f"""
SELECT
    RTRIM(LTRIM(EF.FILIAL)) AS branch,
    CONVERT(VARCHAR(10), EF.DATA_PRODUCAO, 23) AS production_date,
    ({FABRIL_EFICIENCIA_PERCENTUAL_SQL}) AS {FABRIL_KPI_EFFICIENCY_ALIAS}
{OEE_FABRIL_KPI_FROM}
WHERE {where_clause}
"""
    with_sql = f"""
WITH
{std_cte},
CALC AS (
{calc_sql}
)
"""
    return with_sql, std_params + tuple(where_params), "FROM CALC"


def build_oee_fabril_kpi_avg_sql(
    *,
    where_clause: str,
    where_params: tuple,
    branch: str | None = None,
    branches: tuple[str, ...] = DEFAULT_PRODUCTION_BRANCHES,
) -> tuple[str, tuple]:
    """Média simples do % canônico na faixa 0–199 (dashboard produção + SI)."""
    with_sql, params, _ = _build_oee_kpi_base(
        where_clause=where_clause,
        where_params=where_params,
        branch=branch,
        branches=branches,
    )
    range_sql = fabril_kpi_efficiency_in_valid_range_sql()
    sql = f"""
{with_sql}
SELECT
    ROUND(AVG({FABRIL_KPI_EFFICIENCY_ALIAS}), 2) AS oee_pct
FROM CALC
WHERE {range_sql}
"""
    return sql, params


def build_oee_fabril_kpi_by_branch_sql(
    *,
    where_clause: str,
    where_params: tuple,
    branch: str | None = None,
    branches: tuple[str, ...] = DEFAULT_PRODUCTION_BRANCHES,
) -> tuple[str, tuple]:
    with_sql, params, _ = _build_oee_kpi_base(
        where_clause=where_clause,
        where_params=where_params,
        branch=branch,
        branches=branches,
    )
    range_sql = fabril_kpi_efficiency_in_valid_range_sql()
    sql = f"""
{with_sql}
SELECT
    branch,
    ROUND(AVG({FABRIL_KPI_EFFICIENCY_ALIAS}), 2) AS oee_pct
FROM CALC
WHERE {range_sql}
GROUP BY branch
"""
    return sql, params


def build_oee_fabril_kpi_by_day_and_branch_sql(
    *,
    where_clause: str,
    where_params: tuple,
    branch: str | None = None,
    branches: tuple[str, ...] = DEFAULT_PRODUCTION_BRANCHES,
) -> tuple[str, tuple]:
    """Agregação diária com sum/count brutos para derivar OEE do período sem 2º scan."""
    with_sql, params, _ = _build_oee_kpi_base(
        where_clause=where_clause,
        where_params=where_params,
        branch=branch,
        branches=branches,
    )
    range_sql = fabril_kpi_efficiency_in_valid_range_sql()
    sql = f"""
{with_sql}
SELECT
    production_date,
    branch,
    ROUND(AVG({FABRIL_KPI_EFFICIENCY_ALIAS}), 2) AS oee_pct,
    COUNT(*) AS appointment_count,
    SUM({FABRIL_KPI_EFFICIENCY_ALIAS}) AS efficiency_sum,
    COUNT({FABRIL_KPI_EFFICIENCY_ALIAS}) AS efficiency_sample_count
FROM CALC
WHERE {range_sql}
GROUP BY production_date, branch
ORDER BY production_date, branch
"""
    return sql, params


# Fragments estáveis para testes de contrato (contêm a fórmula canônica + view).
OEE_FABRIL_KPI_AVG_SELECT = f"""
SELECT
    ROUND(AVG({FABRIL_KPI_EFFICIENCY_ALIAS}), 2) AS oee_pct
FROM (
    SELECT ({FABRIL_EFICIENCIA_PERCENTUAL_SQL}) AS {FABRIL_KPI_EFFICIENCY_ALIAS}
    {OEE_FABRIL_KPI_FROM}
) CALC
"""

OEE_FABRIL_KPI_BY_BRANCH_SELECT = f"""
SELECT
    RTRIM(LTRIM(EF.FILIAL)) AS branch,
    ROUND(AVG(({FABRIL_EFICIENCIA_PERCENTUAL_SQL})), 2) AS oee_pct
{OEE_FABRIL_KPI_FROM}
"""

OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT = f"""
SELECT
    CONVERT(VARCHAR(10), EF.DATA_PRODUCAO, 23) AS production_date,
    RTRIM(LTRIM(EF.FILIAL)) AS branch,
    ROUND(AVG(({FABRIL_EFICIENCIA_PERCENTUAL_SQL})), 2) AS oee_pct,
    COUNT(*) AS appointment_count,
    SUM(({FABRIL_EFICIENCIA_PERCENTUAL_SQL})) AS efficiency_sum,
    COUNT(({FABRIL_EFICIENCIA_PERCENTUAL_SQL})) AS efficiency_sample_count
{OEE_FABRIL_KPI_FROM}
"""
