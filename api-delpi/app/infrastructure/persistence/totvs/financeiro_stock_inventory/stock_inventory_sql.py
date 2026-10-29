"""SQL builders for the R03/P7 stock-inventory snapshot query.

Reads the month-end Protheus balance snapshot (SB9010) joined to the
product register (SB1010) — the semantics authorized by doc 49 §6. This is
intentionally NOT the supplies estimator (SB9 latest available date + SD3
movement bridge): the competence maps exactly to ``B9_DATA`` and a missing
snapshot must surface as ``source_missing``, never as a substituted month.

Aggregation grain is (branch, warehouse, product): SB9 carries one balance
row per (filial, local, produto) per closing date, and the GROUP BY keeps
the API contract stable even if the source ever emits duplicates.
"""

from __future__ import annotations

from typing import Any

# Filtered grouped universe — every consumer (items page, totals, and both
# summaries) derives from this same grain so aggregates always cover the
# full filtered universe, not just the current page.
_GROUPED_SUBQUERY = """
SELECT RTRIM(S.B9_FILIAL) AS branch_code,
       RTRIM(S.B9_LOCAL) AS warehouse,
       RTRIM(S.B9_COD)   AS product_code,
       RTRIM(P.B1_DESC)  AS description,
       RTRIM(P.B1_TIPO)  AS product_type,
       RTRIM(P.B1_GRUPO) AS product_group,
       RTRIM(P.B1_UM)    AS unit,
       CAST(SUM(S.B9_QINI) AS DECIMAL(28,6)) AS quantity,
       CAST(SUM(S.B9_VINI1) AS DECIMAL(28,6)) AS stock_value
  FROM SB9010 S WITH (NOLOCK)
  LEFT JOIN SB1010 P WITH (NOLOCK)
         ON P.B1_COD = S.B9_COD
        AND P.D_E_L_E_T_ = ''
 WHERE S.D_E_L_E_T_ = ''
   AND S.B9_DATA = ?
{filters}
 GROUP BY S.B9_FILIAL, S.B9_LOCAL, S.B9_COD,
          P.B1_DESC, P.B1_TIPO, P.B1_GRUPO, P.B1_UM
"""

_SNAPSHOT_BRANCH_COUNTS_SQL = """
SELECT RTRIM(S.B9_FILIAL) AS branch_code,
       COUNT_BIG(1) AS row_count
  FROM SB9010 S WITH (NOLOCK)
 WHERE S.D_E_L_E_T_ = ''
   AND S.B9_DATA = ?
{filters}
 GROUP BY S.B9_FILIAL
 ORDER BY S.B9_FILIAL
"""

_ITEMS_SQL = """
SELECT branch_code, warehouse, product_code, description, product_type,
       product_group, unit,
       CAST(quantity AS DECIMAL(28,4)) AS historical_quantity,
       CAST(stock_value AS DECIMAL(28,4)) AS historical_stock_value
  FROM ({grouped}) AGG
 ORDER BY branch_code, warehouse, product_code
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""

_TOTALS_SQL = """
SELECT COUNT_BIG(1) AS item_count,
       CAST(COALESCE(SUM(quantity), 0) AS DECIMAL(28,4)) AS total_quantity,
       CAST(COALESCE(SUM(stock_value), 0) AS DECIMAL(28,4)) AS total_value
  FROM ({grouped}) AGG
"""

_SUMMARY_BY_TYPE_SQL = """
SELECT product_type,
       COUNT_BIG(1) AS item_count,
       CAST(SUM(quantity) AS DECIMAL(28,4)) AS total_quantity,
       CAST(SUM(stock_value) AS DECIMAL(28,4)) AS total_stock_value
  FROM ({grouped}) AGG
 GROUP BY product_type
 ORDER BY product_type
"""

_SUMMARY_BY_WAREHOUSE_SQL = """
SELECT branch_code, warehouse,
       COUNT_BIG(1) AS item_count,
       CAST(SUM(quantity) AS DECIMAL(28,4)) AS total_quantity,
       CAST(SUM(stock_value) AS DECIMAL(28,4)) AS total_stock_value
  FROM ({grouped}) AGG
 GROUP BY branch_code, warehouse
 ORDER BY branch_code, warehouse
"""

# Official P7 composition split (doc 49 / doc 80 §41): ``B9_LOCAL <> '99'``
# is the "EM ESTOQUE" operand; ``B9_LOCAL = '99'`` is the physical WIP slice
# of "EM PROCESSO" (the allocated slice comes from SD3/SC2 — see
# work_in_process_sql). The split runs on the same grouped universe, so the
# totalizers always cover the full scope population.
_P7_TOTALS_SQL = """
SELECT COUNT_BIG(1) AS item_count,
       CAST(COALESCE(SUM(CASE WHEN warehouse <> ? THEN stock_value ELSE 0 END), 0)
            AS DECIMAL(28,6)) AS stock_value,
       CAST(COALESCE(SUM(CASE WHEN warehouse = ? THEN stock_value ELSE 0 END), 0)
            AS DECIMAL(28,6)) AS process_physical_value,
       CAST(COALESCE(SUM(CASE WHEN warehouse <> ? THEN quantity ELSE 0 END), 0)
            AS DECIMAL(28,6)) AS stock_quantity
  FROM ({grouped}) AGG
"""


def _in_clause(column: str, values: tuple[str, ...]) -> tuple[str, list[str]]:
    placeholders = ", ".join("?" for _ in values)
    return f" AND {column} IN ({placeholders})", list(values)


def _filters_and_params(
    *,
    branches: tuple[str, ...],
    product_types: tuple[str, ...] | None,
    warehouse: str | None,
) -> tuple[str, list[Any]]:
    filters: list[str] = []
    params: list[Any] = []
    clause, values = _in_clause("S.B9_FILIAL", branches)
    filters.append(clause)
    params.extend(values)
    if product_types:
        clause, values = _in_clause("P.B1_TIPO", product_types)
        filters.append(clause)
        params.extend(values)
    if warehouse:
        filters.append(" AND RTRIM(S.B9_LOCAL) = ?")
        params.append(warehouse)
    return "\n".join(filters), params


def build_snapshot_branch_counts_query(
    *, snapshot_date: str, branches: tuple[str, ...]
) -> tuple[str, list[Any]]:
    """Unfiltered row count per branch — proves snapshot presence."""
    clause, values = _in_clause("S.B9_FILIAL", branches)
    return _SNAPSHOT_BRANCH_COUNTS_SQL.format(filters=clause), [
        snapshot_date,
        *values,
    ]


def _grouped_query(
    *,
    snapshot_date: str,
    branches: tuple[str, ...],
    product_types: tuple[str, ...] | None,
    warehouse: str | None,
) -> tuple[str, list[Any]]:
    filters, params = _filters_and_params(
        branches=branches, product_types=product_types, warehouse=warehouse
    )
    return _GROUPED_SUBQUERY.format(filters=filters), [snapshot_date, *params]


def build_items_query(
    *,
    snapshot_date: str,
    branches: tuple[str, ...],
    product_types: tuple[str, ...] | None,
    warehouse: str | None,
    page: int,
    page_size: int,
) -> tuple[str, list[Any]]:
    grouped, params = _grouped_query(
        snapshot_date=snapshot_date,
        branches=branches,
        product_types=product_types,
        warehouse=warehouse,
    )
    offset = max(page - 1, 0) * page_size
    return _ITEMS_SQL.format(grouped=grouped), [*params, offset, page_size]


def build_totals_query(
    *,
    snapshot_date: str,
    branches: tuple[str, ...],
    product_types: tuple[str, ...] | None,
    warehouse: str | None,
) -> tuple[str, list[Any]]:
    grouped, params = _grouped_query(
        snapshot_date=snapshot_date,
        branches=branches,
        product_types=product_types,
        warehouse=warehouse,
    )
    return _TOTALS_SQL.format(grouped=grouped), params


def build_summary_by_type_query(
    *,
    snapshot_date: str,
    branches: tuple[str, ...],
    product_types: tuple[str, ...] | None,
    warehouse: str | None,
) -> tuple[str, list[Any]]:
    grouped, params = _grouped_query(
        snapshot_date=snapshot_date,
        branches=branches,
        product_types=product_types,
        warehouse=warehouse,
    )
    return _SUMMARY_BY_TYPE_SQL.format(grouped=grouped), params


def build_summary_by_warehouse_query(
    *,
    snapshot_date: str,
    branches: tuple[str, ...],
    product_types: tuple[str, ...] | None,
    warehouse: str | None,
) -> tuple[str, list[Any]]:
    grouped, params = _grouped_query(
        snapshot_date=snapshot_date,
        branches=branches,
        product_types=product_types,
        warehouse=warehouse,
    )
    return _SUMMARY_BY_WAREHOUSE_SQL.format(grouped=grouped), params


def build_p7_totals_query(
    *,
    snapshot_date: str,
    branches: tuple[str, ...],
    product_types: tuple[str, ...] | None,
    process_warehouse: str,
) -> tuple[str, list[Any]]:
    """Official P7 split on the grouped universe: EM ESTOQUE (``B9_LOCAL``
    different from the process warehouse) + physical WIP (``B9_LOCAL`` equal
    to it). Report-level: the ``warehouse`` item filter does not apply —
    the totalizers always cover the whole scope population."""
    grouped, params = _grouped_query(
        snapshot_date=snapshot_date,
        branches=branches,
        product_types=product_types,
        warehouse=None,
    )
    # The CASE placeholders are textual BEFORE the grouped subquery —
    # their params must come first in the list.
    return _P7_TOTALS_SQL.format(grouped=grouped), [
        process_warehouse,
        process_warehouse,
        process_warehouse,
        *params,
    ]
