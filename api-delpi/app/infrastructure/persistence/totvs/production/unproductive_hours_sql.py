"""SQL builders — horas improdutivas (view BI com DESCRICAO_MOTIVO)."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.production.unproductive_hours_view_scope import (
    FONTE_CUSTO_SEM_CUSTO,
    ITEMS_SORT_VALUES,
    METRIC_COST,
    METRIC_HOURS,
    RANK_BY_COST_CENTER,
    RANK_BY_OPERATION,
    RANK_BY_OPERATOR,
    RANK_BY_PRODUCT,
    RANK_BY_RESOURCE,
    RANK_BY_STOP_REASON,
    RANK_BY_VALUES,
    UNPRODUCTIVE_HOURS_VIEW,
    VALID_UNPRODUCTIVE_HOURS_BRANCHES,
)

SEM_CUSTO_PREDICATE = f"LTRIM(RTRIM(v.FONTE_CUSTO)) = '{FONTE_CUSTO_SEM_CUSTO}'"

METRIC_ORDER_COLUMNS = {
    METRIC_HOURS: "total_horas",
    METRIC_COST: "total_custo",
}

ITEMS_SORT_SQL = {
    "date_desc": "v.DATA_REFERENCIA DESC, v.RECNO DESC",
    "date_asc": "v.DATA_REFERENCIA ASC, v.RECNO ASC",
    "hours_desc": "CAST(v.TEMPO_HORAS AS DECIMAL(18, 4)) DESC, v.DATA_REFERENCIA DESC",
    "hours_asc": "CAST(v.TEMPO_HORAS AS DECIMAL(18, 4)) ASC, v.DATA_REFERENCIA DESC",
    "cost_desc": "CAST(v.VALOR_PARADA_RS AS DECIMAL(18, 2)) DESC, v.DATA_REFERENCIA DESC",
    "cost_asc": "CAST(v.VALOR_PARADA_RS AS DECIMAL(18, 2)) ASC, v.DATA_REFERENCIA DESC",
}


@dataclass(frozen=True, slots=True)
class RankBySpec:
    select_keys: str
    group_by: str
    non_empty_predicate: str


RANK_BY_SPECS: dict[str, RankBySpec] = {
    RANK_BY_STOP_REASON: RankBySpec(
        select_keys=(
            "LTRIM(RTRIM(v.MOTIVO)) AS motivo,\n"
            "            MAX(LTRIM(RTRIM(v.DESCRICAO_MOTIVO))) AS motivo_descricao"
        ),
        group_by="LTRIM(RTRIM(v.MOTIVO))",
        non_empty_predicate="LTRIM(RTRIM(v.MOTIVO)) <> ''",
    ),
    RANK_BY_RESOURCE: RankBySpec(
        select_keys=(
            "LTRIM(RTRIM(v.RECURSO)) AS recurso,\n"
            "            LTRIM(RTRIM(v.CENTRO_CUSTO)) AS centro_custo"
        ),
        group_by="LTRIM(RTRIM(v.RECURSO)), LTRIM(RTRIM(v.CENTRO_CUSTO))",
        non_empty_predicate="LTRIM(RTRIM(v.RECURSO)) <> ''",
    ),
    RANK_BY_COST_CENTER: RankBySpec(
        select_keys="LTRIM(RTRIM(v.CENTRO_CUSTO)) AS centro_custo",
        group_by="LTRIM(RTRIM(v.CENTRO_CUSTO))",
        non_empty_predicate="LTRIM(RTRIM(v.CENTRO_CUSTO)) <> ''",
    ),
    RANK_BY_OPERATOR: RankBySpec(
        select_keys=(
            "LTRIM(RTRIM(v.CODIGO_OPERADOR)) AS codigo_operador,\n"
            "            LTRIM(RTRIM(v.NOME_OPERADOR)) AS nome_operador"
        ),
        group_by=(
            "LTRIM(RTRIM(v.CODIGO_OPERADOR)), LTRIM(RTRIM(v.NOME_OPERADOR))"
        ),
        non_empty_predicate="LTRIM(RTRIM(v.CODIGO_OPERADOR)) <> ''",
    ),
    RANK_BY_PRODUCT: RankBySpec(
        select_keys="LTRIM(RTRIM(v.PRODUTO)) AS produto",
        group_by="LTRIM(RTRIM(v.PRODUTO))",
        non_empty_predicate="LTRIM(RTRIM(v.PRODUTO)) <> ''",
    ),
    RANK_BY_OPERATION: RankBySpec(
        select_keys="LTRIM(RTRIM(v.OPERACAO)) AS operacao",
        group_by="LTRIM(RTRIM(v.OPERACAO))",
        non_empty_predicate="LTRIM(RTRIM(v.OPERACAO)) <> ''",
    ),
}


def _from_view() -> str:
    return f"FROM {UNPRODUCTIVE_HOURS_VIEW} v WITH (NOLOCK)"


def _branch_filter_sql(branch: str | None) -> tuple[str, list[str]]:
    if branch:
        return "LTRIM(RTRIM(v.FILIAL)) = ?", [branch]
    ordered = sorted(VALID_UNPRODUCTIVE_HOURS_BRANCHES)
    placeholders = ", ".join("?" for _ in ordered)
    return f"LTRIM(RTRIM(v.FILIAL)) IN ({placeholders})", list(ordered)


def build_base_where(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    stop_reason: str | None = None,
    resource: str | None = None,
    cost_center: str | None = None,
    operator_code: str | None = None,
) -> tuple[str, tuple]:
    branch_sql, branch_params = _branch_filter_sql(branch)
    clauses = [
        "v.DATA_REFERENCIA >= ?",
        "v.DATA_REFERENCIA <= ?",
        branch_sql,
    ]
    params: list[str] = [start_date, end_date, *branch_params]

    if stop_reason:
        clauses.append("LTRIM(RTRIM(v.MOTIVO)) = ?")
        params.append(stop_reason)

    if resource:
        clauses.append("LTRIM(RTRIM(v.RECURSO)) = ?")
        params.append(resource)

    if cost_center:
        clauses.append("LTRIM(RTRIM(v.CENTRO_CUSTO)) = ?")
        params.append(cost_center)

    if operator_code:
        clauses.append("LTRIM(RTRIM(v.CODIGO_OPERADOR)) = ?")
        params.append(operator_code)

    return " AND ".join(clauses), tuple(params)


def _aggregate_metrics_select() -> str:
    return f"""
            COUNT(*) AS total_apontamentos,
            CAST(SUM(CAST(v.TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas,
            CAST(SUM(CAST(v.VALOR_PARADA_RS AS DECIMAL(18, 2))) AS DECIMAL(18, 2)) AS total_custo,
            SUM(CASE WHEN {SEM_CUSTO_PREDICATE} THEN 1 ELSE 0 END) AS registros_sem_custo,
            CAST(
                SUM(
                    CASE
                        WHEN {SEM_CUSTO_PREDICATE}
                        THEN CAST(v.TEMPO_HORAS AS DECIMAL(18, 4))
                        ELSE CAST(0 AS DECIMAL(18, 4))
                    END
                ) AS DECIMAL(18, 4)
            ) AS horas_sem_custo
    """


def build_summary_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    stop_reason: str | None = None,
    resource: str | None = None,
    cost_center: str | None = None,
    operator_code: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        stop_reason=stop_reason,
        resource=resource,
        cost_center=cost_center,
        operator_code=operator_code,
    )
    return (
        f"""
        SELECT
            {_aggregate_metrics_select()}
        {_from_view()}
        WHERE {where_clause}
        """,
        params,
    )


def build_top_resource_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    stop_reason: str | None = None,
    resource: str | None = None,
    cost_center: str | None = None,
    operator_code: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        stop_reason=stop_reason,
        resource=resource,
        cost_center=cost_center,
        operator_code=operator_code,
    )
    return (
        f"""
        SELECT TOP 1
            LTRIM(RTRIM(v.RECURSO)) AS recurso,
            CAST(SUM(CAST(v.TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas
        {_from_view()}
        WHERE {where_clause}
          AND LTRIM(RTRIM(v.RECURSO)) <> ''
        GROUP BY LTRIM(RTRIM(v.RECURSO))
        ORDER BY total_horas DESC
        """,
        params,
    )


def build_top_operator_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    stop_reason: str | None = None,
    resource: str | None = None,
    cost_center: str | None = None,
    operator_code: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        stop_reason=stop_reason,
        resource=resource,
        cost_center=cost_center,
        operator_code=operator_code,
    )
    return (
        f"""
        SELECT TOP 1
            LTRIM(RTRIM(v.CODIGO_OPERADOR)) AS codigo_operador,
            LTRIM(RTRIM(v.NOME_OPERADOR)) AS nome_operador,
            CAST(SUM(CAST(v.TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas
        {_from_view()}
        WHERE {where_clause}
          AND LTRIM(RTRIM(v.CODIGO_OPERADOR)) <> ''
        GROUP BY LTRIM(RTRIM(v.CODIGO_OPERADOR)), LTRIM(RTRIM(v.NOME_OPERADOR))
        ORDER BY total_horas DESC
        """,
        params,
    )


def build_ranking_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    rank_by: str,
    metric: str = METRIC_HOURS,
    limit: int = 10,
    stop_reason: str | None = None,
    resource: str | None = None,
    cost_center: str | None = None,
    operator_code: str | None = None,
) -> tuple[str, tuple]:
    if rank_by not in RANK_BY_VALUES:
        raise ValueError(f"rank_by inválido: {rank_by}")
    spec = RANK_BY_SPECS[rank_by]
    order_column = METRIC_ORDER_COLUMNS.get(metric, METRIC_ORDER_COLUMNS[METRIC_HOURS])
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        stop_reason=stop_reason,
        resource=resource,
        cost_center=cost_center,
        operator_code=operator_code,
    )
    return (
        f"""
        SELECT TOP {int(limit)}
            {spec.select_keys},
            {_aggregate_metrics_select()}
        {_from_view()}
        WHERE {where_clause}
          AND {spec.non_empty_predicate}
        GROUP BY {spec.group_by}
        ORDER BY {order_column} DESC
        """,
        params,
    )


def build_items_count_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    stop_reason: str | None = None,
    resource: str | None = None,
    cost_center: str | None = None,
    operator_code: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        stop_reason=stop_reason,
        resource=resource,
        cost_center=cost_center,
        operator_code=operator_code,
    )
    return (
        f"""
        SELECT COUNT(*) AS total
        {_from_view()}
        WHERE {where_clause}
        """,
        params,
    )


def resolve_items_order_by(sort: str | None) -> str:
    key = (sort or "date_desc").strip().lower()
    if key not in ITEMS_SORT_VALUES:
        key = "date_desc"
    return ITEMS_SORT_SQL[key]


def build_items_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None,
    sort: str = "date_desc",
    offset: int = 0,
    page_size: int = 50,
    stop_reason: str | None = None,
    resource: str | None = None,
    cost_center: str | None = None,
    operator_code: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        stop_reason=stop_reason,
        resource=resource,
        cost_center=cost_center,
        operator_code=operator_code,
    )
    order_clause = resolve_items_order_by(sort)
    return (
        f"""
        SELECT
            v.DATA_REFERENCIA AS data_referencia,
            LTRIM(RTRIM(v.FILIAL)) AS filial,
            LTRIM(RTRIM(v.OP)) AS op,
            LTRIM(RTRIM(v.PRODUTO)) AS produto,
            LTRIM(RTRIM(v.OPERACAO)) AS operacao,
            LTRIM(RTRIM(v.RECURSO)) AS recurso,
            LTRIM(RTRIM(v.CENTRO_CUSTO)) AS centro_custo,
            LTRIM(RTRIM(v.CODIGO_OPERADOR)) AS codigo_operador,
            LTRIM(RTRIM(v.NOME_OPERADOR)) AS nome_operador,
            LTRIM(RTRIM(v.MOTIVO)) AS motivo,
            LTRIM(RTRIM(v.DESCRICAO_MOTIVO)) AS motivo_descricao,
            LTRIM(RTRIM(v.OBSERVACAO)) AS observacao,
            CAST(v.TEMPO_HORAS AS DECIMAL(18, 4)) AS tempo_horas,
            CAST(v.VALOR_PARADA_RS AS DECIMAL(18, 2)) AS valor_parada,
            LTRIM(RTRIM(v.FONTE_CUSTO)) AS fonte_custo,
            v.RECNO AS recno
        {_from_view()}
        WHERE {where_clause}
        ORDER BY {order_clause}
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """,
        (*params, int(offset), int(page_size)),
    )
