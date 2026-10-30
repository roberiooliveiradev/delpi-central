"""SQL builders for the R11 billing-exclusion roster (doc 126).

Grain: one SD2 item row — the same grain as the historical artifact
``NF a desconsiderar.xlsb`` / ``Planilha2``. The competence axis is
``D2_EMISSAO`` (doc 85 BR-R11-002).

The roster predicate is evaluated row-by-row at the application layer:
the query returns every in-competence SD2 line where ``D2_GRUPO``
matches the roster group OR ``D2_TES`` matches the roster TES — the
union of both observed predicates so the related out-of-criteria
population (DV-R11-04) stays observable next to the candidates.

No join may multiply rows — SF4 is resolved through a TOP 1 OUTER
APPLY (branch-specific register preferred, shared blank-filial
fallback, same mold as ``stock_kardex_sql``); SB1/SA1 are LEFT joins.
Document sibling metrics (item count, stock-moving sibling presence)
are correlated aggregates over the document identity
``D2_FILIAL + D2_DOC + D2_SERIE`` — evaluated per line, never a join.
"""

from __future__ import annotations

from typing import Any

# SF4 TES resolution — one catalog row per TES code, branch-specific
# register preferred over the shared (blank-filial) one; TOP 1 so the
# join never multiplies SD2 lines (same mold as _TES_APPLY in
# stock_kardex_sql.py).
_SF4_APPLY = """
  OUTER APPLY (
      SELECT TOP 1
             RTRIM(F.F4_ESTOQUE) AS f4_stock_movement,
             RTRIM(F.F4_DUPLIC)  AS f4_duplicate_flag,
             RTRIM(F.F4_TEXTO)   AS f4_description
        FROM SF4010 F WITH (NOLOCK)
       WHERE F.D_E_L_E_T_ = ' '
         AND F.F4_CODIGO = D2.D2_TES
         AND (F.F4_FILIAL = D2.D2_FILIAL
              OR RTRIM(F.F4_FILIAL) = '')
       ORDER BY CASE WHEN F.F4_FILIAL = D2.D2_FILIAL
                     THEN 0 ELSE 1 END
  ) SF4
"""

_LINES_SQL = """
SELECT D2.R_E_C_N_O_ AS line_id,
       RTRIM(D2.D2_FILIAL)  AS branch_code,
       RTRIM(D2.D2_DOC)     AS document,
       RTRIM(D2.D2_SERIE)   AS series,
       RTRIM(D2.D2_ITEM)    AS item,
       RTRIM(D2.D2_NUMSEQ)  AS sequence_number,
       RTRIM(D2.D2_COD)     AS product_code,
       RTRIM(P.B1_DESC)     AS product_description,
       RTRIM(D2.D2_TP)      AS product_type,
       RTRIM(D2.D2_GRUPO)   AS product_group,
       RTRIM(D2.D2_TES)     AS tes,
       SF4.f4_description   AS tes_description,
       SF4.f4_stock_movement AS tes_stock_movement,
       SF4.f4_duplicate_flag AS tes_duplicate_flag,
       RTRIM(D2.D2_CF)      AS cf,
       RTRIM(D2.D2_CLIENTE) AS customer_code,
       RTRIM(D2.D2_LOJA)    AS customer_store,
       RTRIM(C.A1_NOME)     AS customer_name,
       RTRIM(D2.D2_CONTA)   AS account_code,
       RTRIM(D2.D2_LOCAL)   AS warehouse,
       RTRIM(D2.D2_PEDIDO)  AS order_number,
       RTRIM(D2.D2_EMISSAO) AS issue_date,
       CAST(D2.D2_QUANT  AS DECIMAL(30,9)) AS quantity,
       CAST(D2.D2_PRCVEN AS DECIMAL(30,9)) AS unit_price,
       CAST(D2.D2_TOTAL  AS DECIMAL(30,9)) AS total_value,
       CAST(D2.D2_CUSTO1 AS DECIMAL(30,9)) AS stock_cost,
       (SELECT COUNT(1)
          FROM SD2010 X WITH (NOLOCK)
         WHERE X.D_E_L_E_T_ = ' '
           AND X.D2_FILIAL = D2.D2_FILIAL
           AND X.D2_DOC    = D2.D2_DOC
           AND X.D2_SERIE  = D2.D2_SERIE) AS document_item_count,
       CASE WHEN EXISTS (
                SELECT 1
                  FROM SD2010 Y WITH (NOLOCK)
                  LEFT JOIN SF4010 FY WITH (NOLOCK)
                         ON FY.F4_CODIGO = Y.D2_TES
                        AND FY.D_E_L_E_T_ = ' '
                        AND (FY.F4_FILIAL = Y.D2_FILIAL
                             OR RTRIM(FY.F4_FILIAL) = '')
                 WHERE Y.D_E_L_E_T_ = ' '
                   AND Y.D2_FILIAL = D2.D2_FILIAL
                   AND Y.D2_DOC    = D2.D2_DOC
                   AND Y.D2_SERIE  = D2.D2_SERIE
                   AND ISNULL(RTRIM(FY.F4_ESTOQUE), '') = 'S'
            ) THEN 1 ELSE 0 END AS has_stock_sibling_item
  FROM SD2010 D2 WITH (NOLOCK)
  LEFT JOIN SB1010 P WITH (NOLOCK)
         ON P.B1_COD = D2.D2_COD
        AND P.D_E_L_E_T_ = ' '
  LEFT JOIN SA1010 C WITH (NOLOCK)
         ON C.A1_COD = D2.D2_CLIENTE
        AND C.A1_LOJA = D2.D2_LOJA
        AND C.D_E_L_E_T_ = ' '
{sf4_apply}
 WHERE D2.D_E_L_E_T_ = ' '
   AND D2.D2_FILIAL IN ({branch_placeholders})
   AND D2.D2_EMISSAO BETWEEN ? AND ?
   AND (RTRIM(D2.D2_GRUPO) = ? OR RTRIM(D2.D2_TES) = ?)
{filters}
"""


def _in_placeholders(values: tuple[str, ...]) -> str:
    return ", ".join("?" for _ in values)


def build_lines_query(
    *,
    period_start: str,
    period_end: str,
    branches: tuple[str, ...],
    roster_product_group: str,
    roster_tes: str,
    product_group: str | None,
    product_code: str | None,
    document: str | None,
    customer_code: str | None,
    tes: str | None,
) -> tuple[str, list[Any]]:
    """In-competence SD2 lines related to the roster criteria.

    The SQL scopes branch, competence axis and the union of the two
    observed predicates (roster group OR roster TES); the
    candidates/out-of-criteria split is applied by the use case over
    these rows. Optional user filters narrow inside that population.
    Deterministic ordering for stable paging.
    """
    filters: list[str] = []
    params: list[Any] = []
    if product_group:
        filters.append("   AND RTRIM(D2.D2_GRUPO) = ?")
        params.append(product_group)
    if product_code:
        filters.append("   AND RTRIM(D2.D2_COD) = ?")
        params.append(product_code)
    if document:
        filters.append("   AND RTRIM(D2.D2_DOC) = ?")
        params.append(document)
    if customer_code:
        filters.append("   AND RTRIM(D2.D2_CLIENTE) = ?")
        params.append(customer_code)
    if tes:
        filters.append("   AND RTRIM(D2.D2_TES) = ?")
        params.append(tes)

    sql = _LINES_SQL.format(
        sf4_apply=_SF4_APPLY,
        branch_placeholders=_in_placeholders(branches),
        filters="\n".join(filters),
    )
    sql += (
        "ORDER BY issue_date, document, series, item, line_id\n"
    )
    return sql, [
        *branches,
        period_start,
        period_end,
        roster_product_group,
        roster_tes,
        *params,
    ]
