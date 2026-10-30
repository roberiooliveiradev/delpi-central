"""SQL builders for the R10 cost-center-expenses engine (doc 126).

Grain: one SD1 item row — the same grain as the historical artifact
``CC matriz.xlsb`` / ``SCAGQGA0.XML``. The competence axis is always
``D1_DTDIGIT`` (documented in doc 85 BR-R10-001; the legacy
``vw_fin_despesas_centro_custo`` view uses ``D1_EMISSAO`` and is NOT
equivalent — REUSE_PARTIAL, doc 126 §4).

The calculation/investigation split is evaluated row-by-row at the
application layer over this unfiltered-within-scope set: the query
returns every in-competence SD1 line for the authorized branches and
carries the raw attributes (``D1_TES``, ``D1_TP``, ``D1_GRUPO``,
``D1_CC``) the selection predicate needs. No join may multiply rows —
CTT is resolved through a TOP 1 OUTER APPLY (branch-specific register
preferred, shared blank-filial fallback, same mold as the SF4 lookup in
``stock_kardex_sql``); SB1/SA2 are LEFT joins so a missing master
register never drops an expense line.
"""

from __future__ import annotations

from typing import Any

# CTT resolution — one catalog row per cost-center code, branch-specific
# register preferred over the shared (blank-filial) one; TOP 1 so the
# join never multiplies SD1 lines (same mold as _TES_APPLY in
# stock_kardex_sql.py).
_CTT_APPLY = """
  OUTER APPLY (
      SELECT TOP 1
             RTRIM(C.CTT_CUSTO)  AS cc_resolved,
             RTRIM(C.CTT_DESC01) AS cc_description,
             RTRIM(C.CTT_CLASSE) AS cc_class_kind,
             RTRIM(C.CTT_BLOQ)   AS cc_blocked
        FROM CTT010 C WITH (NOLOCK)
       WHERE C.D_E_L_E_T_ = ''
         AND RTRIM(C.CTT_CUSTO) = RTRIM(D1.D1_CC)
         AND (C.CTT_FILIAL = D1.D1_FILIAL
              OR RTRIM(C.CTT_FILIAL) = '')
       ORDER BY CASE WHEN C.CTT_FILIAL = D1.D1_FILIAL
                     THEN 0 ELSE 1 END
  ) CTT
"""

_LINES_SQL = """
SELECT D1.R_E_C_N_O_ AS line_id,
       RTRIM(D1.D1_FILIAL)  AS branch_code,
       RTRIM(D1.D1_DOC)     AS document,
       RTRIM(D1.D1_SERIE)   AS series,
       RTRIM(D1.D1_ITEM)    AS item,
       RTRIM(D1.D1_NUMSEQ)  AS sequence_number,
       RTRIM(D1.D1_COD)     AS product_code,
       RTRIM(P.B1_DESC)     AS product_description,
       RTRIM(D1.D1_TP)      AS product_type,
       RTRIM(D1.D1_GRUPO)   AS product_group,
       RTRIM(D1.D1_TIPO)    AS document_type,
       RTRIM(D1.D1_CC)      AS cost_center,
       CTT.cc_description   AS cost_center_description,
       CTT.cc_class_kind    AS cost_center_class_kind,
       CTT.cc_blocked       AS cost_center_blocked,
       RTRIM(D1.D1_CONTA)   AS account_code,
       RTRIM(D1.D1_TES)     AS tes,
       RTRIM(D1.D1_CF)      AS cf,
       RTRIM(D1.D1_FORNECE) AS supplier_code,
       RTRIM(D1.D1_LOJA)    AS supplier_store,
       RTRIM(S.A2_NOME)     AS supplier_name,
       RTRIM(D1.D1_LOCAL)   AS warehouse,
       RTRIM(D1.D1_PEDIDO)  AS order_number,
       RTRIM(D1.D1_DTDIGIT) AS entry_date,
       RTRIM(D1.D1_EMISSAO) AS issue_date,
       CAST(D1.D1_QUANT  AS DECIMAL(30,9)) AS quantity,
       CAST(D1.D1_VUNIT  AS DECIMAL(30,9)) AS unit_value,
       CAST(D1.D1_TOTAL  AS DECIMAL(30,9)) AS total_value
  FROM SD1010 D1 WITH (NOLOCK)
  LEFT JOIN SB1010 P WITH (NOLOCK)
         ON P.B1_COD = D1.D1_COD
        AND P.D_E_L_E_T_ = ' '
  LEFT JOIN SA2010 S WITH (NOLOCK)
         ON S.A2_COD = D1.D1_FORNECE
        AND S.A2_LOJA = D1.D1_LOJA
        AND S.D_E_L_E_T_ = ' '
{ctt_apply}
 WHERE D1.D_E_L_E_T_ = ' '
   AND D1.D1_FILIAL IN ({branch_placeholders})
   AND D1.D1_DTDIGIT BETWEEN ? AND ?
{filters}
"""


def _in_placeholders(values: tuple[str, ...]) -> str:
    return ", ".join("?" for _ in values)


def build_lines_query(
    *,
    period_start: str,
    period_end: str,
    branches: tuple[str, ...],
    cost_center: str | None,
    product_code: str | None,
    document: str | None,
    supplier_code: str | None,
    tes: str | None,
) -> tuple[str, list[Any]]:
    """Every in-competence SD1 line for the authorized branches.

    The official/investigation split is applied by the use case over
    these rows — the SQL only scopes branch, competence axis and the
    optional user filters (deterministic ordering for stable paging).
    """
    filters: list[str] = []
    params: list[Any] = []
    if cost_center:
        filters.append("   AND RTRIM(D1.D1_CC) = ?")
        params.append(cost_center)
    if product_code:
        filters.append("   AND RTRIM(D1.D1_COD) = ?")
        params.append(product_code)
    if document:
        filters.append("   AND RTRIM(D1.D1_DOC) = ?")
        params.append(document)
    if supplier_code:
        filters.append("   AND RTRIM(D1.D1_FORNECE) = ?")
        params.append(supplier_code)
    if tes:
        filters.append("   AND RTRIM(D1.D1_TES) = ?")
        params.append(tes)

    sql = _LINES_SQL.format(
        ctt_apply=_CTT_APPLY,
        branch_placeholders=_in_placeholders(branches),
        filters="\n".join(filters),
    )
    sql += (
        "ORDER BY entry_date, document, sequence_number, item, line_id\n"
    )
    return sql, [*branches, period_start, period_end, *params]
