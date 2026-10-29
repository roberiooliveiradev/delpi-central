"""SQL builders for the R05 stock-movements summary (MATR320/MAT056 rule).

Canonical rules proven in doc 85 §5 (matr320.prx fonte + 130/130 official
cells reconciled for competence 09/2026, filial 01):

- SD1 (BR-R05-003/004): ``F4_ESTOQUE='S'`` TES join, window by
  ``D1_DTDIGIT``, ``D1_ORIGLAN<>'LF'``, value ``D1_CUSTO``;
  ``F4_PODER3='N'`` + ``D1_TIPO<>'D'`` → purchases; ``TIPO='D'`` →
  sales returns; ``F4_PODER3<>'N'`` → third-party in.
- SD2 (BR-R05-003/004): ``F4_ESTOQUE='S'``, window by ``D2_EMISSAO``,
  ``D2_ORIGLAN<>'LF'``, value ``D2_CUSTO1``; ``TIPO<>'D'`` → sales;
  ``TIPO='D'`` → purchase returns; ``F4_PODER3<>'N'`` → third-party out.
- SD3 (BR-R05-003/005): ``D3_EMISSAO`` in the window,
  ``D3_ESTORNO<>'S'``, signed ``D3_CUSTO1`` (negative when
  ``D3_TM > '500'``); classification order — ``PR*`` → production;
  ``{RE4,DE4}`` → transfers; empty OP + ``D3_CF[3]<>'3'`` → internal
  movements; filled OP → production requisitions; remainder → process
  transfers (memo column, outside the balance equation).
- Precision (BR-R05-012): ``D*_CUSTO*`` are ``float(53)`` — every line
  value is cast to ``DECIMAL(30,9)`` BEFORE the SUM; aggregating floats
  first masks real micro-adjustments.

The closing balance (SA) is intentionally NOT computed here — it comes
from the same SB9 grouped universe the P7 engine reads
(``stock_inventory_sql``), so both reports measure the identical
as_of population.
"""

from __future__ import annotations

from typing import Any

# TES resolution: prefer a branch-specific SF4 row, fall back to the
# shared (blank-filial) register — TOP 1 keeps the join from
# multiplying movement rows when both registers exist.
_TES_APPLY = """
  OUTER APPLY (
      SELECT TOP 1
             RTRIM(F4.F4_PODER3) AS poder3,
             RTRIM(F4.F4_ESTOQUE) AS estoque
        FROM SF4010 F4 WITH (NOLOCK)
       WHERE F4.D_E_L_E_T_ = ''
         AND F4.F4_CODIGO = {tes_column}
         AND (F4.F4_FILIAL = {filial_column}
              OR RTRIM(F4.F4_FILIAL) = '')
       ORDER BY CASE WHEN F4.F4_FILIAL = {filial_column}
                     THEN 0 ELSE 1 END
  ) TES
"""

_SD1_SQL = """
SELECT RTRIM(P.B1_TIPO) AS product_type,
       CAST(SUM(CASE WHEN TES.poder3 = 'N' AND RTRIM(D1.D1_TIPO) <> 'D'
                     THEN CAST(D1.D1_CUSTO AS DECIMAL(30,9))
                     ELSE 0 END) AS DECIMAL(28,6)) AS purchases,
       CAST(SUM(CASE WHEN TES.poder3 = 'N' AND RTRIM(D1.D1_TIPO) = 'D'
                     THEN CAST(D1.D1_CUSTO AS DECIMAL(30,9))
                     ELSE 0 END) AS DECIMAL(28,6)) AS sales_returns,
       CAST(SUM(CASE WHEN TES.poder3 <> 'N'
                     THEN CAST(D1.D1_CUSTO AS DECIMAL(30,9))
                     ELSE 0 END) AS DECIMAL(28,6)) AS third_party_in
  FROM SD1010 D1 WITH (NOLOCK)
{tes_apply}
  LEFT JOIN SB1010 P WITH (NOLOCK)
         ON P.B1_COD = D1.D1_COD
        AND P.D_E_L_E_T_ = ' '
 WHERE D1.D_E_L_E_T_ = ' '
   AND TES.estoque = 'S'
   AND D1.D1_FILIAL IN ({branch_placeholders})
   AND D1.D1_DTDIGIT BETWEEN ? AND ?
   AND D1.D1_ORIGLAN <> 'LF'
{type_filter}
 GROUP BY RTRIM(P.B1_TIPO)
"""

_SD2_SQL = """
SELECT RTRIM(P.B1_TIPO) AS product_type,
       CAST(SUM(CASE WHEN TES.poder3 = 'N' AND RTRIM(D2.D2_TIPO) <> 'D'
                     THEN CAST(D2.D2_CUSTO1 AS DECIMAL(30,9))
                     ELSE 0 END) AS DECIMAL(28,6)) AS sales,
       CAST(SUM(CASE WHEN TES.poder3 = 'N' AND RTRIM(D2.D2_TIPO) = 'D'
                     THEN CAST(D2.D2_CUSTO1 AS DECIMAL(30,9))
                     ELSE 0 END) AS DECIMAL(28,6)) AS purchase_returns,
       CAST(SUM(CASE WHEN TES.poder3 <> 'N'
                     THEN CAST(D2.D2_CUSTO1 AS DECIMAL(30,9))
                     ELSE 0 END) AS DECIMAL(28,6)) AS third_party_out
  FROM SD2010 D2 WITH (NOLOCK)
{tes_apply}
  LEFT JOIN SB1010 P WITH (NOLOCK)
         ON P.B1_COD = D2.D2_COD
        AND P.D_E_L_E_T_ = ' '
 WHERE D2.D_E_L_E_T_ = ' '
   AND TES.estoque = 'S'
   AND D2.D2_FILIAL IN ({branch_placeholders})
   AND D2.D2_EMISSAO BETWEEN ? AND ?
   AND D2.D2_ORIGLAN <> 'LF'
{type_filter}
 GROUP BY RTRIM(P.B1_TIPO)
"""

# SD3 movements classified per BR-R05-005 precedence — the CASE order IS
# the business rule; do not reorder.
_SD3_SQL = """
SELECT product_type,
       CAST(SUM(CASE WHEN cls = 'production' THEN valor ELSE 0 END)
            AS DECIMAL(28,6)) AS production,
       CAST(SUM(CASE WHEN cls = 'transfers' THEN valor ELSE 0 END)
            AS DECIMAL(28,6)) AS transfers,
       CAST(SUM(CASE WHEN cls = 'internal' THEN valor ELSE 0 END)
            AS DECIMAL(28,6)) AS internal_movements,
       CAST(SUM(CASE WHEN cls = 'requisition' THEN valor ELSE 0 END)
            AS DECIMAL(28,6)) AS production_requisitions,
       CAST(SUM(CASE WHEN cls = 'process_memo' THEN valor ELSE 0 END)
            AS DECIMAL(28,6)) AS process_transfers
  FROM (
    SELECT RTRIM(P.B1_TIPO) AS product_type,
           CASE
             WHEN RTRIM(D3.D3_CF) LIKE 'PR%' THEN 'production'
             WHEN RTRIM(D3.D3_CF) IN ('RE4', 'DE4') THEN 'transfers'
             WHEN NULLIF(LTRIM(RTRIM(D3.D3_OP)), '') IS NULL
                  AND SUBSTRING(D3.D3_CF, 3, 1) <> '3' THEN 'internal'
             WHEN NULLIF(LTRIM(RTRIM(D3.D3_OP)), '') IS NOT NULL
                  THEN 'requisition'
             ELSE 'process_memo'
           END AS cls,
           CASE WHEN D3.D3_TM > '500'
                THEN -CAST(D3.D3_CUSTO1 AS DECIMAL(30,9))
                ELSE CAST(D3.D3_CUSTO1 AS DECIMAL(30,9))
           END AS valor
      FROM SD3010 D3 WITH (NOLOCK)
      LEFT JOIN SB1010 P WITH (NOLOCK)
             ON P.B1_COD = D3.D3_COD
            AND P.D_E_L_E_T_ = ' '
     WHERE D3.D_E_L_E_T_ = ' '
       AND D3.D3_FILIAL IN ({branch_placeholders})
       AND D3.D3_EMISSAO BETWEEN ? AND ?
       AND D3.D3_ESTORNO <> 'S'
  ) mov
{type_filter}
 GROUP BY product_type
"""


def _in_placeholders(values: tuple[str, ...]) -> str:
    return ", ".join("?" for _ in values)


def _type_filter(product_types: tuple[str, ...] | None, alias: str) -> tuple[str, list[str]]:
    if not product_types:
        return "", []
    clause = (
        " WHERE product_type IN ("
        + _in_placeholders(product_types)
        + ")"
        if alias == "outer"
        else "   AND RTRIM(P.B1_TIPO) IN ("
        + _in_placeholders(product_types)
        + ")"
    )
    return clause, list(product_types)


def build_sd1_by_type_query(
    *,
    branches: tuple[str, ...],
    period_start: str,
    period_end: str,
    product_types: tuple[str, ...] | None,
) -> tuple[str, list[Any]]:
    tes_apply = _TES_APPLY.format(
        tes_column="D1.D1_TES", filial_column="D1.D1_FILIAL"
    )
    type_filter, type_params = _type_filter(product_types, "inner")
    sql = _SD1_SQL.format(
        tes_apply=tes_apply,
        branch_placeholders=_in_placeholders(branches),
        type_filter=type_filter,
    )
    return sql, [*branches, period_start, period_end, *type_params]


def build_sd2_by_type_query(
    *,
    branches: tuple[str, ...],
    period_start: str,
    period_end: str,
    product_types: tuple[str, ...] | None,
) -> tuple[str, list[Any]]:
    tes_apply = _TES_APPLY.format(
        tes_column="D2.D2_TES", filial_column="D2.D2_FILIAL"
    )
    type_filter, type_params = _type_filter(product_types, "inner")
    sql = _SD2_SQL.format(
        tes_apply=tes_apply,
        branch_placeholders=_in_placeholders(branches),
        type_filter=type_filter,
    )
    return sql, [*branches, period_start, period_end, *type_params]


def build_sd3_by_type_query(
    *,
    branches: tuple[str, ...],
    period_start: str,
    period_end: str,
    product_types: tuple[str, ...] | None,
) -> tuple[str, list[Any]]:
    # SD3 classifies inside a derived table — the product_type filter
    # applies on the outer SELECT.
    type_filter, type_params = _type_filter(product_types, "outer")
    sql = _SD3_SQL.format(
        branch_placeholders=_in_placeholders(branches),
        type_filter=type_filter,
    )
    return sql, [*branches, period_start, period_end, *type_params]
