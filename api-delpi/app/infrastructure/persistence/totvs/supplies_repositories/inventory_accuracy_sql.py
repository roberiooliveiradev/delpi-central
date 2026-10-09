"""SQL — acuracidade do inventário físico (SB7 eventos × SD3 doc='INVENT').

Evento oficial = (B7_FILIAL, B7_COD, B7_LOCAL, B7_DATA); linhas físicas do
mesmo evento agregam por SUM(B7_QUANT). Pareamento com ajustes segue a mesma
chave canônica do inventory_adjustments_repository (filial+produto+armazém
+data). Teórico oficial por evento = contado + furo - sobra (a autoridade é
o ajuste emitido pelo MATA270, não a reconstrução SB9+SD3).
"""

from __future__ import annotations

from typing import Any, Sequence

from app.domain.totvs.protheus_internal_movements import (
    INVENTORY_ADJUSTMENT_DOCUMENT,
    MOVEMENT_TYPE_INBOUND_THRESHOLD,
)

_SORT_MAP = {
    "count_date_desc": "count_date DESC, product_code ASC",
    "count_date_asc": "count_date ASC, product_code ASC",
    "product_code_asc": "product_code ASC",
    "product_code_desc": "product_code DESC",
    "divergence_value_desc": (
        "(shortage_value + surplus_value) DESC, product_code ASC"
    ),
}
DEFAULT_SORT = "count_date_desc"

_INBOUND = MOVEMENT_TYPE_INBOUND_THRESHOLD  # '500' — TM < 500 = sobra/entrada


def _in_placeholders(values: Sequence[str]) -> str:
    return ", ".join("?" for _ in values)


def build_events_cte(
    *,
    branches: Sequence[str],
    period_start: str,
    period_end_exclusive: str,
) -> tuple[str, list[Any]]:
    """CTE `evaluated` — um evento por (filial, produto, armazém, data)."""
    branch_ph = _in_placeholders(branches)
    params: list[Any] = [*branches, period_start, period_end_exclusive,
                       *branches, period_start, period_end_exclusive]

    sql = f"""
WITH events AS (
    SELECT
        S.B7_FILIAL AS branch,
        RTRIM(S.B7_COD) AS product_code,
        RTRIM(S.B7_LOCAL) AS warehouse,
        S.B7_DATA AS count_date,
        SUM(CAST(S.B7_QUANT AS DECIMAL(18,6))) AS counted_quantity,
        MAX(RTRIM(ISNULL(S.B7_STATUS, ''))) AS count_status,
        MAX(NULLIF(LTRIM(RTRIM(S.B7_DOC)), '')) AS inventory_document,
        COUNT(*) AS physical_lines
    FROM SB7010 S WITH (NOLOCK)
    WHERE S.D_E_L_E_T_ = ''
      AND S.B7_FILIAL IN ({branch_ph})
      AND S.B7_DATA >= ?
      AND S.B7_DATA < ?
    GROUP BY S.B7_FILIAL, S.B7_COD, S.B7_LOCAL, S.B7_DATA
),
adjustments AS (
    SELECT
        D.D3_FILIAL AS branch,
        D.D3_COD AS product_code,
        D.D3_LOCAL AS warehouse,
        D.D3_EMISSAO AS count_date,
        SUM(CASE WHEN D.D3_TM >= '{_INBOUND}'
                 THEN CAST(D.D3_QUANT AS DECIMAL(18,6)) ELSE 0 END)
            AS shortage_quantity,
        SUM(CASE WHEN D.D3_TM < '{_INBOUND}'
                 THEN CAST(D.D3_QUANT AS DECIMAL(18,6)) ELSE 0 END)
            AS surplus_quantity,
        SUM(CASE WHEN D.D3_TM >= '{_INBOUND}'
                 THEN ABS(D.D3_CUSTO1) ELSE 0 END) AS shortage_value,
        SUM(CASE WHEN D.D3_TM < '{_INBOUND}'
                 THEN ABS(D.D3_CUSTO1) ELSE 0 END) AS surplus_value,
        COUNT(*) AS adjustment_rows
    FROM SD3010 D WITH (NOLOCK)
    JOIN events e
      ON e.branch = D.D3_FILIAL
     AND e.product_code = D.D3_COD
     AND e.warehouse = D.D3_LOCAL
     AND e.count_date = D.D3_EMISSAO
    WHERE D.D_E_L_E_T_ = ''
      AND RTRIM(ISNULL(D.D3_ESTORNO, '')) <> 'S'
      AND RTRIM(LTRIM(D.D3_DOC)) = '{INVENTORY_ADJUSTMENT_DOCUMENT}'
      AND D.D3_FILIAL IN ({branch_ph})
      AND D.D3_EMISSAO >= ?
      AND D.D3_EMISSAO < ?
    GROUP BY D.D3_FILIAL, D.D3_COD, D.D3_LOCAL, D.D3_EMISSAO
),
evaluated AS (
    SELECT
        e.branch,
        e.product_code,
        RTRIM(ISNULL(SB1.B1_DESC, '')) AS description,
        RTRIM(SB1.B1_UM) AS unit_of_measure,
        CASE WHEN RTRIM(SB1.B1_MSBLQL) = '1' THEN 1 ELSE 0 END AS blocked,
        e.warehouse,
        e.count_date,
        e.counted_quantity,
        e.count_status,
        e.inventory_document,
        e.physical_lines,
        ISNULL(a.shortage_quantity, 0) AS shortage_quantity,
        ISNULL(a.surplus_quantity, 0) AS surplus_quantity,
        ISNULL(a.shortage_value, 0) AS shortage_value,
        ISNULL(a.surplus_value, 0) AS surplus_value,
        ISNULL(a.adjustment_rows, 0) AS adjustment_rows,
        e.counted_quantity
          + ISNULL(a.shortage_quantity, 0)
          - ISNULL(a.surplus_quantity, 0) AS theoretical_quantity,
        CASE
            WHEN e.count_status <> '2' THEN 'excluded'
            WHEN a.adjustment_rows IS NULL THEN 'accurate'
            ELSE 'divergent'
        END AS outcome,
        CASE WHEN e.count_status <> '2'
             THEN 'pending_processing' END AS exclusion_reason
    FROM events e
    LEFT JOIN adjustments a
      ON a.branch = e.branch
     AND a.product_code = e.product_code
     AND a.warehouse = e.warehouse
     AND a.count_date = e.count_date
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
      ON SB1.B1_COD = e.product_code AND SB1.D_E_L_E_T_ = ''
)
"""
    return sql, params


def build_summary_queries(
    *,
    branches: Sequence[str],
    period_start: str,
    period_end_exclusive: str,
) -> tuple[str, list[Any]]:
    """CTE materializada em #evaluated + 2 resultsets (totais/filial)."""
    cte, params = build_events_cte(
        branches=branches,
        period_start=period_start,
        period_end_exclusive=period_end_exclusive,
    )
    combined = cte + """
SELECT * INTO #evaluated FROM evaluated;

SELECT
    COUNT(*) AS valid_count_total,
    SUM(CASE WHEN outcome IN ('accurate','divergent')
             THEN 1 ELSE 0 END) AS evaluable_count_total,
    SUM(CASE WHEN outcome = 'accurate' THEN 1 ELSE 0 END) AS accurate_count,
    SUM(CASE WHEN outcome = 'divergent' THEN 1 ELSE 0 END) AS divergent_count,
    SUM(CASE WHEN outcome = 'excluded' THEN 1 ELSE 0 END) AS excluded_count,
    SUM(CASE WHEN exclusion_reason = 'pending_processing'
             THEN 1 ELSE 0 END) AS excluded_pending_processing,
    SUM(shortage_value) AS shortage_value_total,
    SUM(surplus_value) AS surplus_value_total
FROM #evaluated;

SELECT branch,
       COUNT(*) AS valid_count_total,
       SUM(CASE WHEN outcome IN ('accurate','divergent')
                THEN 1 ELSE 0 END) AS evaluable_count_total,
       SUM(CASE WHEN outcome = 'accurate' THEN 1 ELSE 0 END)
           AS accurate_count,
       SUM(CASE WHEN outcome = 'divergent' THEN 1 ELSE 0 END)
           AS divergent_count,
       SUM(CASE WHEN outcome = 'excluded' THEN 1 ELSE 0 END)
           AS excluded_count,
       SUM(shortage_value) AS shortage_value_total,
       SUM(surplus_value) AS surplus_value_total
FROM #evaluated
GROUP BY branch;

DROP TABLE #evaluated;
"""
    return combined, params


def _items_where(outcome: str | None) -> tuple[str, list[Any]]:
    if outcome:
        return "WHERE outcome = ?", [outcome]
    return "", []


def build_count_query(
    *,
    branches: Sequence[str],
    period_start: str,
    period_end_exclusive: str,
    outcome: str | None,
) -> tuple[str, list[Any]]:
    cte, params = build_events_cte(
        branches=branches,
        period_start=period_start,
        period_end_exclusive=period_end_exclusive,
    )
    where, where_params = _items_where(outcome)
    return (
        cte + f"SELECT COUNT(*) AS total FROM evaluated {where};",
        [*params, *where_params],
    )


def build_items_query(
    *,
    branches: Sequence[str],
    period_start: str,
    period_end_exclusive: str,
    outcome: str | None,
    sort: str,
    offset: int,
    page_size: int,
) -> tuple[str, list[Any]]:
    cte, params = build_events_cte(
        branches=branches,
        period_start=period_start,
        period_end_exclusive=period_end_exclusive,
    )
    where, where_params = _items_where(outcome)
    order = _SORT_MAP.get(sort, _SORT_MAP[DEFAULT_SORT])
    sql = cte + f"""
SELECT branch, product_code, description, unit_of_measure, blocked,
       warehouse, count_date, counted_quantity, theoretical_quantity,
       shortage_quantity, surplus_quantity, shortage_value, surplus_value,
       adjustment_rows, physical_lines, inventory_document, count_status,
       outcome, exclusion_reason
FROM evaluated
{where}
ORDER BY {order}
OFFSET {int(offset)} ROWS FETCH NEXT {int(page_size)} ROWS ONLY;
"""
    return sql, [*params, *where_params]


def build_last_closing_query(branches: Sequence[str]) -> tuple[str, list[Any]]:
    branch_ph = _in_placeholders(branches)
    sql = f"""
SELECT MAX(B9.B9_DATA) AS last_closing
FROM SB9010 B9 WITH (NOLOCK)
WHERE B9.D_E_L_E_T_ = ''
  AND B9.B9_FILIAL IN ({branch_ph});
"""
    return sql, list(branches)


def build_cancelled_count_query(
    *,
    branches: Sequence[str],
    period_start: str,
    period_end_exclusive: str,
) -> tuple[str, list[Any]]:
    branch_ph = _in_placeholders(branches)
    sql = f"""
SELECT COUNT(*) AS cancelled_count
FROM (
    SELECT S.B7_FILIAL, S.B7_COD, S.B7_LOCAL, S.B7_DATA
    FROM SB7010 S WITH (NOLOCK)
    WHERE S.D_E_L_E_T_ <> ''
      AND S.B7_FILIAL IN ({branch_ph})
      AND S.B7_DATA >= ?
      AND S.B7_DATA < ?
    GROUP BY S.B7_FILIAL, S.B7_COD, S.B7_LOCAL, S.B7_DATA
) c;
"""
    return sql, [*branches, period_start, period_end_exclusive]
