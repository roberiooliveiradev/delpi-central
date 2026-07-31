"""SQL builders — VW_PCP_ORDENS_PRODUCAO."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.production.pcp_orders_view_scope import (
    FLAG_YES_TEXT,
    ITEMS_SORT_VALUES,
    METRIC_BALANCE,
    METRIC_DELAY_DAYS,
    METRIC_ORDER_QTY,
    METRIC_REPORTED_QTY,
    METRIC_VALUES,
    PCP_ORDERS_VIEW,
    RANK_BY_OP,
    RANK_BY_PRODUCT,
    RANK_BY_VALUES,
    RANK_BY_WAREHOUSE,
    VALID_PCP_ORDERS_BRANCHES,
)

METRIC_ORDER_COLUMNS = {
    METRIC_ORDER_QTY: "order_qty_sum",
    METRIC_REPORTED_QTY: "reported_qty_sum",
    METRIC_BALANCE: "balance_sum",
    METRIC_DELAY_DAYS: "avg_days_late",
}

ITEMS_SORT_SQL = {
    "delivery_desc": "v.DT_ENTREGA DESC, v.OP_CHAVE DESC",
    "delivery_asc": "v.DT_ENTREGA ASC, v.OP_CHAVE ASC",
    "issue_desc": "v.DT_EMISSAO DESC, v.OP_CHAVE DESC",
    "issue_asc": "v.DT_EMISSAO ASC, v.OP_CHAVE ASC",
    "delay_desc": "CAST(v.DIAS_ATRASO AS INT) DESC, v.OP_CHAVE DESC",
    "delay_asc": "CAST(v.DIAS_ATRASO AS INT) ASC, v.OP_CHAVE ASC",
    "qty_desc": "CAST(v.QTD_ORDEM AS DECIMAL(18, 6)) DESC, v.OP_CHAVE DESC",
    "qty_asc": "CAST(v.QTD_ORDEM AS DECIMAL(18, 6)) ASC, v.OP_CHAVE ASC",
    "op_asc": "v.OP_CHAVE ASC",
    "op_desc": "v.OP_CHAVE DESC",
}


@dataclass(frozen=True, slots=True)
class RankBySpec:
    select_keys: str
    group_by: str
    non_empty_predicate: str


RANK_BY_SPECS: dict[str, RankBySpec] = {
    RANK_BY_PRODUCT: RankBySpec(
        select_keys=(
            "LTRIM(RTRIM(v.PRODUTO)) AS product_code,\n"
            "            MAX(LTRIM(RTRIM(v.DESC_PRODUTO))) AS product_description"
        ),
        group_by="LTRIM(RTRIM(v.PRODUTO))",
        non_empty_predicate="LTRIM(RTRIM(v.PRODUTO)) <> ''",
    ),
    RANK_BY_WAREHOUSE: RankBySpec(
        select_keys="LTRIM(RTRIM(v.ARMAZEM)) AS warehouse",
        group_by="LTRIM(RTRIM(v.ARMAZEM))",
        non_empty_predicate="LTRIM(RTRIM(ISNULL(v.ARMAZEM, ''))) <> ''",
    ),
    RANK_BY_OP: RankBySpec(
        select_keys=(
            "LTRIM(RTRIM(v.OP_CHAVE)) AS op_key,\n"
            "            MAX(LTRIM(RTRIM(v.PRODUTO))) AS product_code,\n"
            "            MAX(LTRIM(RTRIM(v.DESC_PRODUTO))) AS product_description"
        ),
        group_by="LTRIM(RTRIM(v.OP_CHAVE))",
        non_empty_predicate="LTRIM(RTRIM(v.OP_CHAVE)) <> ''",
    ),
}


def _from_view() -> str:
    return f"FROM {PCP_ORDERS_VIEW} v WITH (NOLOCK)"


def _branch_filter_sql(branch: str | None) -> tuple[str, list[str]]:
    if branch:
        return "LTRIM(RTRIM(v.FILIAL)) = ?", [branch]
    ordered = sorted(VALID_PCP_ORDERS_BRANCHES)
    placeholders = ", ".join("?" for _ in ordered)
    return f"LTRIM(RTRIM(v.FILIAL)) IN ({placeholders})", list(ordered)


def build_base_where(
    *,
    delivery_start: str,
    delivery_end: str,
    branch: str | None,
    actual_end_start: str | None = None,
    actual_end_end: str | None = None,
    op_key: str | None = None,
    product_code: str | None = None,
    warehouse: str | None = None,
    mother_only: bool | None = None,
    open_only: bool | None = None,
    delayed_only: bool | None = None,
) -> tuple[str, tuple]:
    branch_sql, branch_params = _branch_filter_sql(branch)
    clauses = [
        "v.DT_ENTREGA IS NOT NULL",
        "v.DT_ENTREGA >= ?",
        "v.DT_ENTREGA <= ?",
        branch_sql,
    ]
    params: list = [delivery_start, delivery_end, *branch_params]

    if actual_end_start:
        clauses.append("v.DT_REAL_FIM IS NOT NULL AND v.DT_REAL_FIM >= ?")
        params.append(actual_end_start)
    if actual_end_end:
        clauses.append("v.DT_REAL_FIM IS NOT NULL AND v.DT_REAL_FIM <= ?")
        params.append(actual_end_end)
    if op_key:
        clauses.append("LTRIM(RTRIM(v.OP_CHAVE)) LIKE ?")
        params.append(f"%{op_key.strip()}%")
    if product_code:
        clauses.append("LTRIM(RTRIM(v.PRODUTO)) LIKE ?")
        params.append(f"%{product_code.strip()}%")
    if warehouse:
        clauses.append("LTRIM(RTRIM(v.ARMAZEM)) = ?")
        params.append(warehouse.strip())
    if mother_only is True:
        clauses.append("v.FL_OP_MAE = 1")
    elif mother_only is False:
        clauses.append("ISNULL(v.FL_OP_MAE, 0) = 0")
    if open_only is True:
        clauses.append("v.FL_OP_EM_ABERTO = 1")
    elif open_only is False:
        clauses.append("ISNULL(v.FL_OP_EM_ABERTO, 0) = 0")
    if delayed_only is True:
        clauses.append(f"LTRIM(RTRIM(v.FL_ATRASADA)) = '{FLAG_YES_TEXT}'")
    elif delayed_only is False:
        clauses.append(
            f"(v.FL_ATRASADA IS NULL OR LTRIM(RTRIM(v.FL_ATRASADA)) <> '{FLAG_YES_TEXT}')"
        )

    return " AND ".join(clauses), tuple(params)


def _aggregate_select() -> str:
    return f"""
            COUNT(*) AS total_orders,
            SUM(CASE WHEN v.FL_OP_EM_ABERTO = 1 THEN 1 ELSE 0 END) AS open_orders,
            SUM(
                CASE
                    WHEN LTRIM(RTRIM(v.FL_ATRASADA)) = '{FLAG_YES_TEXT}' THEN 1
                    ELSE 0
                END
            ) AS delayed_orders,
            SUM(CASE WHEN v.FL_OP_MAE = 1 THEN 1 ELSE 0 END) AS mother_orders,
            CAST(SUM(CAST(v.QTD_ORDEM AS DECIMAL(18, 6))) AS DECIMAL(18, 6)) AS planned_qty_sum,
            CAST(SUM(CAST(v.QTD_APONTADA AS DECIMAL(18, 6))) AS DECIMAL(18, 6)) AS produced_qty_sum,
            CAST(SUM(CAST(v.SALDO_OP AS DECIMAL(18, 6))) AS DECIMAL(18, 6)) AS pending_qty_sum,
            CAST(AVG(CAST(v.DIAS_ATRASO AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS avg_days_late,
            CAST(MAX(CAST(v.DIAS_ATRASO AS INT)) AS INT) AS max_days_late
    """


def build_summary_query(**filters) -> tuple[str, tuple]:
    where_sql, params = build_base_where(**filters)
    query = f"""
        SELECT
            {_aggregate_select()}
        {_from_view()}
        WHERE {where_sql}
    """
    return query, params


def build_items_count_query(**filters) -> tuple[str, tuple]:
    where_sql, params = build_base_where(**filters)
    query = f"""
        SELECT COUNT(*) AS total
        {_from_view()}
        WHERE {where_sql}
    """
    return query, params


def build_items_query(
    *,
    sort: str,
    offset: int,
    page_size: int,
    **filters,
) -> tuple[str, tuple]:
    if sort not in ITEMS_SORT_VALUES:
        raise ValueError(f"sort inválido: {sort}")
    where_sql, params = build_base_where(**filters)
    order_sql = ITEMS_SORT_SQL[sort]
    query = f"""
        SELECT
            LTRIM(RTRIM(v.FILIAL)) AS filial,
            LTRIM(RTRIM(v.OP_CHAVE)) AS op_chave,
            LTRIM(RTRIM(v.OP_NUM)) AS op_num,
            LTRIM(RTRIM(v.OP_ITEM)) AS op_item,
            LTRIM(RTRIM(v.OP_SEQUEN)) AS op_sequen,
            LTRIM(RTRIM(v.OP_PAI_CHAVE)) AS op_pai_chave,
            LTRIM(RTRIM(v.PRODUTO)) AS produto,
            LTRIM(RTRIM(v.DESC_PRODUTO)) AS desc_produto,
            LTRIM(RTRIM(v.PRODUTO_DESCRICAO)) AS produto_descricao,
            LTRIM(RTRIM(v.ARMAZEM)) AS armazem,
            LTRIM(RTRIM(v.OBSERVACOES)) AS observacoes,
            CAST(v.QTD_ORDEM AS DECIMAL(18, 6)) AS qtd_ordem,
            CAST(v.QTD_APONTADA AS DECIMAL(18, 6)) AS qtd_apontada,
            CAST(v.SALDO_OP AS DECIMAL(18, 6)) AS saldo_op,
            CAST(v.QTD_PERDA AS DECIMAL(18, 6)) AS qtd_perda,
            v.DT_EMISSAO AS dt_emissao,
            v.DT_INICIO AS dt_inicio,
            v.DT_ENTREGA AS dt_entrega,
            v.DT_REAL_FIM AS dt_real_fim,
            CAST(v.DIAS_ATRASO AS INT) AS dias_atraso,
            v.FL_OP_EM_ABERTO AS fl_op_em_aberto,
            v.FL_OP_MAE AS fl_op_mae,
            LTRIM(RTRIM(v.FL_ATRASADA)) AS fl_atrasada,
            LTRIM(RTRIM(v.FL_TEM_SALDO)) AS fl_tem_saldo,
            LTRIM(RTRIM(v.SITUACAO_PRODUCAO)) AS situacao_producao,
            LTRIM(RTRIM(v.TIPO_OP)) AS tipo_op,
            LTRIM(RTRIM(v.TIPO_OP_COD)) AS tipo_op_cod
        {_from_view()}
        WHERE {where_sql}
        ORDER BY {order_sql}
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    return query, (*params, offset, page_size)


def build_ranking_query(
    *,
    rank_by: str,
    metric: str,
    limit: int,
    **filters,
) -> tuple[str, tuple]:
    if rank_by not in RANK_BY_VALUES:
        raise ValueError(f"rank_by inválido: {rank_by}")
    if metric not in METRIC_VALUES:
        raise ValueError(f"metric inválida: {metric}")
    spec = RANK_BY_SPECS[rank_by]
    where_sql, params = build_base_where(**filters)
    order_col = METRIC_ORDER_COLUMNS[metric]
    query = f"""
        SELECT TOP {int(limit)}
            {spec.select_keys},
            COUNT(*) AS total_orders,
            CAST(SUM(CAST(v.QTD_ORDEM AS DECIMAL(18, 6))) AS DECIMAL(18, 6)) AS order_qty_sum,
            CAST(SUM(CAST(v.QTD_APONTADA AS DECIMAL(18, 6))) AS DECIMAL(18, 6)) AS reported_qty_sum,
            CAST(SUM(CAST(v.SALDO_OP AS DECIMAL(18, 6))) AS DECIMAL(18, 6)) AS balance_sum,
            CAST(AVG(CAST(v.DIAS_ATRASO AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS avg_days_late,
            CAST(MAX(CAST(v.DIAS_ATRASO AS INT)) AS INT) AS max_days_late
        {_from_view()}
        WHERE {where_sql}
          AND {spec.non_empty_predicate}
        GROUP BY {spec.group_by}
        ORDER BY {order_col} DESC
    """
    return query, params
