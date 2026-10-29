"""SQL builders for the P7 "EM PROCESSO" allocated slice (MATR989 rule).

Canonical composition proven in doc 80 §41/errata (MATR989 analytical
artifact, Dt.Ref 01/10/2026):

- per (branch, product, production order) the balance is
  ``SUM(D3_CUSTO1)`` of ``D3_CF LIKE 'RE%'`` movements minus
  ``D3_CF LIKE 'DE%'`` movements, restricted to ``D3_EMISSAO`` on or
  before the month-end snapshot date;
- a pair is reported only when the order is alive at emission: no
  ``D3_CF LIKE 'PR%'`` (production posting) on or before the
  emission-day cutoff, and not cancelled-without-producing in SC2
  (``C2_QUJE = 0`` and ``C2_DATRF`` set on or before the same cutoff);
- the scope filter is the same canonical ``B1_TIPO`` selection used by
  the snapshot engine — one engine, two product selections.

The SB9 warehouse-99 physical slice is computed separately by
``stock_inventory_sql.build_p7_totals_query``; the MATR989 "sem-OP"
block reconciles 1:1 with it (doc 80 §41.D).
"""

from __future__ import annotations

from typing import Any

_REQUISITION_CF_PATTERN = "RE%"
_DEVOLUTION_CF_PATTERN = "DE%"
_PRODUCTION_CF_PATTERN = "PR%"

# Net balance per (branch, product, OP) at the movement cutoff.
_MOV_CTE = """
WITH mov AS (
  SELECT D3.D3_FILIAL AS branch_code,
         RTRIM(D3.D3_COD) AS product_code,
         D3.D3_OP AS production_order,
         SUM(CASE WHEN D3.D3_CF LIKE ? THEN CAST(D3.D3_CUSTO1 AS DECIMAL(28,8))
                  WHEN D3.D3_CF LIKE ? THEN -CAST(D3.D3_CUSTO1 AS DECIMAL(28,8))
                  ELSE 0 END) AS allocated_value,
         SUM(CASE WHEN D3.D3_CF LIKE ? THEN CAST(D3.D3_QUANT AS DECIMAL(28,8))
                  WHEN D3.D3_CF LIKE ? THEN -CAST(D3.D3_QUANT AS DECIMAL(28,8))
                  ELSE 0 END) AS allocated_quantity
    FROM SD3010 D3 WITH (NOLOCK)
   WHERE D3.D_E_L_E_T_ = ' '
     AND D3.D3_FILIAL IN ({branch_placeholders})
     AND D3.D3_EMISSAO <= ?
     AND (D3.D3_CF LIKE ? OR D3.D3_CF LIKE ?)
     AND NULLIF(LTRIM(RTRIM(D3.D3_OP)), '') IS NOT NULL
   GROUP BY D3.D3_FILIAL, D3.D3_COD, D3.D3_OP
)
"""

# OP alive at emission: no production posting on/before the emission
# cutoff AND not cancelled-without-producing (SC2 QUJE=0 + DATRF set on
# or before the cutoff). DATRF filled after the cutoff keeps the OP
# alive at emission — post-emission finishes must not erase the as_of
# state.
_ALIVE_PREDICATE = """
    AND NOT EXISTS (
        SELECT 1
          FROM SD3010 P3 WITH (NOLOCK)
         WHERE P3.D_E_L_E_T_ = ' '
           AND P3.D3_FILIAL = m.branch_code
           AND P3.D3_OP = m.production_order
           AND P3.D3_CF LIKE ?
           AND P3.D3_EMISSAO <= ?
    )
    AND NOT EXISTS (
        SELECT 1
          FROM SC2010 C2 WITH (NOLOCK)
         WHERE C2.D_E_L_E_T_ = ' '
           AND C2.C2_FILIAL = m.branch_code
           AND RTRIM(C2.C2_OP) = RTRIM(m.production_order)
           AND C2.C2_QUJE = 0
           AND NULLIF(LTRIM(RTRIM(C2.C2_DATRF)), '') IS NOT NULL
           AND C2.C2_DATRF <= ?
    )
"""

_ALLOCATED_BY_TYPE_SQL = _MOV_CTE + """
SELECT RTRIM(P.B1_TIPO) AS product_type,
       CAST(SUM(m.allocated_value) AS DECIMAL(28,6)) AS allocated_value,
       COUNT_BIG(DISTINCT m.production_order) AS open_order_count
  FROM mov m
  LEFT JOIN SB1010 P WITH (NOLOCK)
         ON P.B1_COD = m.product_code
        AND P.D_E_L_E_T_ = ' '
 WHERE m.allocated_value <> 0
{alive}
{type_filter}
 GROUP BY RTRIM(P.B1_TIPO)
"""


def _in_placeholders(values: tuple[str, ...]) -> str:
    return ", ".join("?" for _ in values)


def build_work_in_process_by_type_query(
    *,
    branches: tuple[str, ...],
    product_types: tuple[str, ...] | None,
    movement_cutoff: str,
    op_alive_cutoff: str,
) -> tuple[str, list[Any]]:
    """Allocated WIP per product type for the scope population.

    ``movement_cutoff`` is the month-end snapshot date (YYYYMMDD);
    ``op_alive_cutoff`` is the emission-day convention (snapshot date +
    1 day) — OPs whose first PR0 lands on the emission day itself are
    excluded, matching the official emission behaviour (doc 80 §41.C).
    """
    type_filter = ""
    params: list[Any] = [
        _REQUISITION_CF_PATTERN,
        _DEVOLUTION_CF_PATTERN,
        _REQUISITION_CF_PATTERN,
        _DEVOLUTION_CF_PATTERN,
        *branches,
        movement_cutoff,
        _REQUISITION_CF_PATTERN,
        _DEVOLUTION_CF_PATTERN,
    ]
    alive_params: list[Any] = [
        _PRODUCTION_CF_PATTERN,
        op_alive_cutoff,
        op_alive_cutoff,
    ]
    if product_types:
        type_filter = (
            "   AND RTRIM(P.B1_TIPO) IN ("
            + _in_placeholders(product_types)
            + ")"
        )
    sql = _ALLOCATED_BY_TYPE_SQL.format(
        branch_placeholders=_in_placeholders(branches),
        alive=_ALIVE_PREDICATE,
        type_filter=type_filter,
    )
    type_params = list(product_types) if product_types else []
    return sql, [*params, *alive_params, *type_params]


# Standalone R08 detail (MATR989 com-OP block): one row per
# (branch, product, production order) alive at the emission cutoff —
# same CTE, same alive predicate as the P7 composition.
_DETAIL_SQL = _MOV_CTE + """
SELECT m.branch_code,
       RTRIM(m.product_code) AS product_code,
       RTRIM(P.B1_DESC) AS description,
       RTRIM(P.B1_TIPO) AS product_type,
       m.production_order,
       CAST(m.allocated_quantity AS DECIMAL(28,6)) AS allocated_quantity,
       CAST(m.allocated_value AS DECIMAL(28,6)) AS allocated_value
  FROM mov m
  LEFT JOIN SB1010 P WITH (NOLOCK)
         ON P.B1_COD = m.product_code
        AND P.D_E_L_E_T_ = ' '
 WHERE m.allocated_value <> 0
{alive}
{type_filter}
 ORDER BY m.branch_code, m.product_code, m.production_order
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""

_DETAIL_COUNT_SQL = _MOV_CTE + """
SELECT COUNT_BIG(1) AS item_count
  FROM mov m
  LEFT JOIN SB1010 P WITH (NOLOCK)
         ON P.B1_COD = m.product_code
        AND P.D_E_L_E_T_ = ' '
 WHERE m.allocated_value <> 0
{alive}
{type_filter}
"""


def _detail_query(
    *,
    template: str,
    branches: tuple[str, ...],
    product_types: tuple[str, ...] | None,
    movement_cutoff: str,
    op_alive_cutoff: str,
) -> tuple[str, list[Any]]:
    type_filter = ""
    params: list[Any] = [
        _REQUISITION_CF_PATTERN,
        _DEVOLUTION_CF_PATTERN,
        _REQUISITION_CF_PATTERN,
        _DEVOLUTION_CF_PATTERN,
        *branches,
        movement_cutoff,
        _REQUISITION_CF_PATTERN,
        _DEVOLUTION_CF_PATTERN,
    ]
    alive_params: list[Any] = [
        _PRODUCTION_CF_PATTERN,
        op_alive_cutoff,
        op_alive_cutoff,
    ]
    if product_types:
        type_filter = (
            "   AND RTRIM(P.B1_TIPO) IN ("
            + _in_placeholders(product_types)
            + ")"
        )
    sql = template.format(
        branch_placeholders=_in_placeholders(branches),
        alive=_ALIVE_PREDICATE,
        type_filter=type_filter,
    )
    type_params = list(product_types) if product_types else []
    return sql, [*params, *alive_params, *type_params]


def build_work_in_process_detail_query(
    *,
    branches: tuple[str, ...],
    product_types: tuple[str, ...] | None,
    movement_cutoff: str,
    op_alive_cutoff: str,
    page: int,
    page_size: int,
) -> tuple[str, list[Any]]:
    """MATR989 com-OP detail rows, paginated."""
    sql, params = _detail_query(
        template=_DETAIL_SQL,
        branches=branches,
        product_types=product_types,
        movement_cutoff=movement_cutoff,
        op_alive_cutoff=op_alive_cutoff,
    )
    offset = max(page - 1, 0) * page_size
    return sql, [*params, offset, page_size]


def build_work_in_process_detail_count_query(
    *,
    branches: tuple[str, ...],
    product_types: tuple[str, ...] | None,
    movement_cutoff: str,
    op_alive_cutoff: str,
) -> tuple[str, list[Any]]:
    """Total detail rows for pagination — never a page-bounded count."""
    return _detail_query(
        template=_DETAIL_COUNT_SQL,
        branches=branches,
        product_types=product_types,
        movement_cutoff=movement_cutoff,
        op_alive_cutoff=op_alive_cutoff,
    )
