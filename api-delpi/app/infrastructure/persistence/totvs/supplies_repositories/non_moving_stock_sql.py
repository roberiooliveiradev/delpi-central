"""SQL — matérias-primas sem giro (SB2 × utilização efetiva SD3 × cobertura SB9/SD3).

Elegível: SB2 QATU>0, B1_TIPO='MP', filiais/armazéns do escopo aprovado.
Utilização efetiva: grupo (filial+produto+doc+data) com saída líquida > 0,
conforme spec canônica em domain.totvs.protheus_internal_movements.
Cobertura: primeira evidência de existência = MIN(1º SD3, 1º fechamento SB9).
"""

from __future__ import annotations

from typing import Any, Sequence

from app.domain.totvs.protheus_internal_movements import (
    effective_utilization_base_predicates,
    effective_utilization_net_quantity_sql,
)

_TIEBREAKER = "branch ASC, product_code ASC, warehouse ASC"

_SORT_MAP = {
    "stock_value_desc": f"stock_value DESC, {_TIEBREAKER}",
    "stock_value_asc": f"stock_value ASC, {_TIEBREAKER}",
    "quantity_desc": f"quantity DESC, {_TIEBREAKER}",
    "quantity_asc": f"quantity ASC, {_TIEBREAKER}",
    "product_code_asc": f"product_code ASC, {_TIEBREAKER}",
    "product_code_desc": f"product_code DESC, {_TIEBREAKER}",
    "last_utilization_asc": (
        "CASE WHEN last_effective_utilization IS NULL THEN 1 ELSE 0 END, "
        f"last_effective_utilization ASC, {_TIEBREAKER}"
    ),
    "last_utilization_desc": (
        "CASE WHEN last_effective_utilization IS NULL THEN 1 ELSE 0 END, "
        f"last_effective_utilization DESC, {_TIEBREAKER}"
    ),
}
DEFAULT_SORT = "stock_value_desc"


def _in_placeholders(values: Sequence[str]) -> str:
    return ", ".join("?" for _ in values)


def build_classified_cte(
    *,
    branches: Sequence[str],
    warehouses: Sequence[str],
    window_start: str,
    window_end: str,
    no_consumption_status: str,
    product_codes: Sequence[str] | None = None,
) -> tuple[str, list[Any]]:
    """CTE `classified` — uma linha por produto×filial×armazém elegível.

    Params retornados na ordem dos placeholders do SQL.
    """
    params: list[Any] = []

    branch_ph = _in_placeholders(branches)
    warehouse_ph = _in_placeholders(warehouses)

    product_filter = ""
    if product_codes:
        product_filter = (
            f" AND RTRIM(SB2.B2_COD) IN ({_in_placeholders(product_codes)})"
        )

    util_predicates = "\n      AND ".join(
        effective_utilization_base_predicates("D3")
    )
    net_qty = effective_utilization_net_quantity_sql("D3")

    eligible_params: list[Any] = [*branches, *warehouses]
    if product_codes:
        eligible_params += list(product_codes)

    # eligible_params ×2 (eligible CTE + eligible_keys join não consome params)
    # util join consome branch list de novo? não — filial já vem do join.
    params.extend(eligible_params)
    # window bounds (last_util): in-window check + before-end check
    params.extend([window_start, window_end, window_end])
    # coverage_start > window_start → insufficient; senão status sem giro
    params.extend([window_start, no_consumption_status])

    sql = f"""
WITH eligible AS (
    SELECT
        RTRIM(SB2.B2_FILIAL) AS branch,
        RTRIM(SB2.B2_COD)    AS product_code,
        RTRIM(SB2.B2_LOCAL)  AS warehouse,
        CAST(SB2.B2_QATU AS DECIMAL(18,6)) AS quantity,
        CAST(SB2.B2_CM1  AS DECIMAL(18,6)) AS unit_cost,
        CAST(SB2.B2_QATU AS DECIMAL(18,6))
          * CAST(SB2.B2_CM1 AS DECIMAL(18,6)) AS stock_value,
        RTRIM(ISNULL(SB1.B1_DESC, '')) AS description,
        RTRIM(SB1.B1_UM) AS unit_of_measure,
        CASE WHEN RTRIM(SB1.B1_MSBLQL) = '1' THEN 1 ELSE 0 END AS blocked
    FROM SB2010 SB2 WITH (NOLOCK)
    JOIN SB1010 SB1 WITH (NOLOCK)
      ON SB1.B1_COD = SB2.B2_COD
     AND SB1.D_E_L_E_T_ = ''
     AND RTRIM(SB1.B1_TIPO) = 'MP'
    WHERE SB2.D_E_L_E_T_ = ''
      AND SB2.B2_QATU > 0
      AND RTRIM(SB2.B2_FILIAL) IN ({branch_ph})
      AND RTRIM(SB2.B2_LOCAL) IN ({warehouse_ph}){product_filter}
),
eligible_keys AS (
    SELECT DISTINCT branch, product_code FROM eligible
),
util_groups AS (
    SELECT
        D3.D3_FILIAL AS branch,
        RTRIM(D3.D3_COD) AS product_code,
        D3.D3_EMISSAO AS utilization_date,
        SUM({net_qty}) AS net_outbound
    FROM SD3010 D3 WITH (NOLOCK)
    JOIN eligible_keys ek
      ON ek.branch = D3.D3_FILIAL
     AND ek.product_code = D3.D3_COD
    WHERE {util_predicates}
    GROUP BY D3.D3_FILIAL, D3.D3_COD, D3.D3_DOC, D3.D3_EMISSAO
    HAVING SUM({net_qty}) > 0
),
last_util AS (
    SELECT
        branch,
        product_code,
        MAX(CASE WHEN utilization_date >= ? AND utilization_date <= ?
                 THEN utilization_date END) AS last_util_in_window,
        MAX(CASE WHEN utilization_date <= ?
                 THEN utilization_date END) AS last_util_before_end
    FROM util_groups
    GROUP BY branch, product_code
),
coverage AS (
    SELECT branch, product_code, MIN(evidence_date) AS coverage_start
    FROM (
        SELECT D3.D3_FILIAL AS branch, RTRIM(D3.D3_COD) AS product_code,
               MIN(D3.D3_EMISSAO) AS evidence_date
        FROM SD3010 D3 WITH (NOLOCK)
        JOIN eligible_keys ek
          ON ek.branch = D3.D3_FILIAL
         AND ek.product_code = D3.D3_COD
        WHERE D3.D_E_L_E_T_ = ''
        GROUP BY D3.D3_FILIAL, D3.D3_COD
        UNION ALL
        SELECT B9.B9_FILIAL, RTRIM(B9.B9_COD), MIN(B9.B9_DATA)
        FROM SB9010 B9 WITH (NOLOCK)
        JOIN eligible_keys ek
          ON ek.branch = B9.B9_FILIAL
         AND ek.product_code = B9.B9_COD
        WHERE B9.D_E_L_E_T_ = ''
        GROUP BY B9.B9_FILIAL, B9.B9_COD
    ) ev
    GROUP BY branch, product_code
),
classified AS (
    SELECT
        e.branch,
        e.product_code,
        e.warehouse,
        e.quantity,
        e.unit_cost,
        e.stock_value,
        e.description,
        e.unit_of_measure,
        e.blocked,
        lu.last_util_in_window,
        lu.last_util_before_end AS last_effective_utilization,
        CASE
            WHEN lu.last_util_in_window IS NOT NULL THEN 'WITH_CONSUMPTION'
            WHEN cov.coverage_start IS NULL
              OR cov.coverage_start > ?
            THEN 'INSUFFICIENT_HISTORY'
            ELSE ?
        END AS turnover_status
    FROM eligible e
    LEFT JOIN last_util lu
      ON lu.branch = e.branch AND lu.product_code = e.product_code
    LEFT JOIN coverage cov
      ON cov.branch = e.branch AND cov.product_code = e.product_code
)
"""
    return sql, params


def build_summary_queries(
    *,
    branches: Sequence[str],
    warehouses: Sequence[str],
    window_start: str,
    window_end: str,
    no_consumption_status: str,
) -> tuple[str, list[Any]]:
    """CTE materializada em #classified + 3 resultsets (totais/status/filial)."""
    cte, params = build_classified_cte(
        branches=branches,
        warehouses=warehouses,
        window_start=window_start,
        window_end=window_end,
        no_consumption_status=no_consumption_status,
    )
    combined = cte + """
SELECT * INTO #classified FROM classified;

SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT branch + '|' + product_code) AS product_count,
    SUM(stock_value) AS eligible_stock_value,
    SUM(CASE WHEN turnover_status = 'INSUFFICIENT_HISTORY'
             THEN stock_value ELSE 0 END) AS insufficient_history_stock_value,
    SUM(CASE WHEN turnover_status IN ('NO_CONSUMPTION_12M',
             'NO_CONSUMPTION_IN_PERIOD')
             THEN stock_value ELSE 0 END) AS no_consumption_stock_value,
    SUM(CASE WHEN turnover_status = 'WITH_CONSUMPTION'
             THEN stock_value ELSE 0 END) AS with_consumption_stock_value,
    SUM(CASE WHEN blocked = 1 THEN stock_value ELSE 0 END)
        AS blocked_stock_value,
    SUM(CASE WHEN blocked = 1
              AND turnover_status IN ('NO_CONSUMPTION_12M',
                  'NO_CONSUMPTION_IN_PERIOD')
             THEN stock_value ELSE 0 END) AS blocked_no_consumption_stock_value,
    COUNT(DISTINCT CASE WHEN blocked = 1
             THEN branch + '|' + product_code END) AS blocked_product_count,
    COUNT(DISTINCT CASE WHEN turnover_status = 'WITH_CONSUMPTION'
             THEN branch + '|' + product_code END) AS with_consumption_count,
    COUNT(DISTINCT CASE WHEN turnover_status IN ('NO_CONSUMPTION_12M',
             'NO_CONSUMPTION_IN_PERIOD')
             THEN branch + '|' + product_code END) AS no_consumption_count,
    COUNT(DISTINCT CASE WHEN turnover_status = 'INSUFFICIENT_HISTORY'
             THEN branch + '|' + product_code END)
        AS insufficient_history_count,
    COUNT(DISTINCT CASE WHEN unit_cost = 0
             THEN branch + '|' + product_code + '|' + warehouse END)
        AS zero_cost_item_count
FROM #classified;

SELECT turnover_status,
       COUNT(DISTINCT branch + '|' + product_code) AS product_count,
       SUM(stock_value) AS stock_value,
       SUM(CASE WHEN blocked = 1 THEN stock_value ELSE 0 END)
           AS blocked_stock_value
FROM #classified
GROUP BY turnover_status;

SELECT branch,
       COUNT(DISTINCT product_code) AS product_count,
       SUM(stock_value) AS eligible_stock_value,
       SUM(CASE WHEN turnover_status IN ('NO_CONSUMPTION_12M',
                'NO_CONSUMPTION_IN_PERIOD')
                THEN stock_value ELSE 0 END) AS no_consumption_stock_value,
       SUM(CASE WHEN turnover_status = 'INSUFFICIENT_HISTORY'
                THEN stock_value ELSE 0 END) AS insufficient_history_stock_value,
       SUM(CASE WHEN blocked = 1 THEN stock_value ELSE 0 END)
           AS blocked_stock_value
FROM #classified
GROUP BY branch;

DROP TABLE #classified;
"""
    return combined, params


def _like_escape(term: str) -> str:
    """Escapa curingas LIKE — busca sempre literal."""
    return (
        term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )


def build_items_where(
    *,
    turnover_status: str | None,
    blocked: bool | None,
    search: str | None,
) -> tuple[str, list[Any]]:
    where: list[str] = []
    params: list[Any] = []
    if turnover_status:
        where.append("turnover_status = ?")
        params.append(turnover_status)
    if blocked is not None:
        where.append("blocked = ?")
        params.append(1 if blocked else 0)
    if search:
        where.append(
            "(product_code LIKE ? ESCAPE '\\' "
            "OR description LIKE ? ESCAPE '\\')"
        )
        pattern = f"%{_like_escape(search)}%"
        params.extend([pattern, pattern])
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    return clause, params


def build_count_query(
    *,
    branches: Sequence[str],
    warehouses: Sequence[str],
    window_start: str,
    window_end: str,
    no_consumption_status: str,
    product_codes: Sequence[str] | None,
    turnover_status: str | None,
    blocked: bool | None,
    search: str | None,
) -> tuple[str, list[Any]]:
    cte, params = build_classified_cte(
        branches=branches,
        warehouses=warehouses,
        window_start=window_start,
        window_end=window_end,
        no_consumption_status=no_consumption_status,
        product_codes=product_codes,
    )
    where, where_params = build_items_where(
        turnover_status=turnover_status, blocked=blocked, search=search
    )
    sql = (
        cte
        + f"SELECT COUNT(*) AS total FROM classified {where};"
    )
    return sql, [*params, *where_params]


def build_items_query(
    *,
    branches: Sequence[str],
    warehouses: Sequence[str],
    window_start: str,
    window_end: str,
    no_consumption_status: str,
    product_codes: Sequence[str] | None,
    turnover_status: str | None,
    blocked: bool | None,
    search: str | None,
    sort: str,
    offset: int,
    page_size: int,
) -> tuple[str, list[Any]]:
    cte, params = build_classified_cte(
        branches=branches,
        warehouses=warehouses,
        window_start=window_start,
        window_end=window_end,
        no_consumption_status=no_consumption_status,
        product_codes=product_codes,
    )
    where, where_params = build_items_where(
        turnover_status=turnover_status, blocked=blocked, search=search
    )
    order = _SORT_MAP.get(sort, _SORT_MAP[DEFAULT_SORT])
    sql = (
        cte
        + f"""
SELECT branch, product_code, description, unit_of_measure, warehouse,
       quantity, unit_cost, stock_value, blocked,
       turnover_status, last_effective_utilization, last_util_in_window
FROM classified
{where}
ORDER BY {order}
OFFSET {int(offset)} ROWS FETCH NEXT {int(page_size)} ROWS ONLY;
"""
    )
    return sql, [*params, *where_params]
