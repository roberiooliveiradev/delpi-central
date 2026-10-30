"""SQL builders for the R06/R07 stock-kardex movement engine (MATR910).

Canonical rules proven against ``matr910_dlp.prx`` (doc 83) and the
09/2026 artifacts (doc 85 §6-§7, 9.357/9.357 movements reconciled):

- UNION of SD1 (inbound, ``D1_DTDIGIT``), SD2 (outbound, ``D2_EMISSAO``)
  and SD3 (internal, ``D3_EMISSAO``) — asymmetric date fields, always;
- SD1/SD2 join SF4 by TES and require ``F4_ESTOQUE='S'`` (branch-specific
  SF4 preferred over the shared register, same OUTER APPLY as the R05
  mold — no row multiplication);
- SD1 requires ``D1_REMITO=''`` and both SD1/SD2 exclude
  ``*_ORIGLAN='LF'``;
- SD3 excludes ``D3_ESTORNO='S'`` when the ``MV_D3ESTOR`` param is 'N',
  and applies the ``D3_SERVIC``/``MV_CQ`` service clause
  (``MV_D3SERVI='N'`` + integrated distribution);
- SB1 master join is INNER — movements without a product register are
  outside the report population; the ``MV_PRODIMP`` product is excluded;
- devolution flags (``MV_LISTDEV=T``): SD1 ``TIPONF='D'`` with a matching
  SF1 header, SD2 ``TIPONF='D'`` with a matching SF2 header;
- cost fields ``D1_CUSTO``/``D2_CUSTO1``/``D3_CUSTO1`` (mv_par11=1; SD1
  carries no numeric suffix for currency 1)
  are ``float(53)`` — cast to ``DECIMAL(30,9)`` per line before any
  aggregation (BR-R05-012 applies to the same fields);
- ordering is deterministic — product, movement date, sequence, recno.

Column selection follows the producer's union (matr910_dlp.prx lines
615-745): CF comes from ``D*_CF``, REF fields (supplier / order /
OP / CC / project) are carried raw and decoded at the data owner.
"""

from __future__ import annotations

from typing import Any

# TES resolution identical to the R05/R03 mold: branch-specific SF4 row
# first, shared (blank-filial) register as fallback, TOP 1 so the join
# never multiplies movement rows.
_TES_APPLY = """
  OUTER APPLY (
      SELECT TOP 1
             RTRIM(F4.F4_CODIGO) AS tm_resolved,
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

_SD1_PART = """
SELECT 'SD1' AS source_table,
       D1.R_E_C_N_O_ AS movement_id,
       RTRIM(D1.D1_FILIAL) AS branch_code,
       RTRIM(D1.D1_LOCAL) AS warehouse,
       RTRIM(D1.D1_COD) AS product_code,
       RTRIM(P.B1_DESC) AS description,
       RTRIM(P.B1_TIPO) AS product_type,
       RTRIM(P.B1_GRUPO) AS product_group,
       RTRIM(P.B1_UM) AS unit,
       RTRIM(D1.D1_DOC) AS document,
       RTRIM(D1.D1_SERIE) AS series,
       RTRIM(D1.D1_DTDIGIT) AS movement_date,
       RTRIM(D1.D1_NUMSEQ) AS sequence_number,
       RTRIM(D1.D1_TES) AS tm,
       RTRIM(D1.D1_CF) AS cf,
       RTRIM(D1.D1_FORNECE) AS partner_code,
       RTRIM(D1.D1_LOJA) AS partner_store,
       '' AS order_number,
       RTRIM(D1.D1_TIPO) AS document_type,
       '' AS project_code,
       '' AS production_order,
       '' AS cost_center,
       CAST(D1.D1_QUANT AS DECIMAL(30,9)) AS quantity,
       CAST(D1.D1_CUSTO AS DECIMAL(30,9)) AS total_cost,
       CASE WHEN RTRIM(D1.D1_TIPO) = 'D' AND DEV.R_E_C_N_O_ IS NOT NULL
            THEN 1 ELSE 0 END AS is_return
  FROM SD1010 D1 WITH (NOLOCK)
{tes_apply}
 INNER JOIN SB1010 P WITH (NOLOCK)
         ON P.B1_COD = D1.D1_COD
        AND P.D_E_L_E_T_ = ' '
  LEFT JOIN SF1010 DEV WITH (NOLOCK)
         ON DEV.F1_FILIAL = D1.D1_FILIAL
        AND DEV.F1_DOC = D1.D1_DOC
        AND DEV.F1_SERIE = D1.D1_SERIE
        AND DEV.F1_FORNECE = D1.D1_FORNECE
        AND DEV.F1_LOJA = D1.D1_LOJA
        AND DEV.D_E_L_E_T_ = ' '
 WHERE D1.D_E_L_E_T_ = ' '
   AND TES.estoque = 'S'
   AND D1.D1_FILIAL IN ({branch_placeholders})
   AND D1.D1_DTDIGIT BETWEEN ? AND ?
   AND D1.D1_ORIGLAN <> 'LF'
   AND D1.D1_REMITO = ''
{filters}
"""

_SD2_PART = """
SELECT 'SD2' AS source_table,
       D2.R_E_C_N_O_ AS movement_id,
       RTRIM(D2.D2_FILIAL) AS branch_code,
       RTRIM(D2.D2_LOCAL) AS warehouse,
       RTRIM(D2.D2_COD) AS product_code,
       RTRIM(P.B1_DESC) AS description,
       RTRIM(P.B1_TIPO) AS product_type,
       RTRIM(P.B1_GRUPO) AS product_group,
       RTRIM(P.B1_UM) AS unit,
       RTRIM(D2.D2_DOC) AS document,
       RTRIM(D2.D2_SERIE) AS series,
       RTRIM(D2.D2_EMISSAO) AS movement_date,
       RTRIM(D2.D2_NUMSEQ) AS sequence_number,
       RTRIM(D2.D2_TES) AS tm,
       RTRIM(D2.D2_CF) AS cf,
       RTRIM(D2.D2_CLIENTE) AS partner_code,
       RTRIM(D2.D2_LOJA) AS partner_store,
       RTRIM(D2.D2_PEDIDO) AS order_number,
       RTRIM(D2.D2_TIPO) AS document_type,
       '' AS project_code,
       '' AS production_order,
       '' AS cost_center,
       CAST(D2.D2_QUANT AS DECIMAL(30,9)) AS quantity,
       CAST(D2.D2_CUSTO1 AS DECIMAL(30,9)) AS total_cost,
       CASE WHEN RTRIM(D2.D2_TIPO) = 'D' AND DEV.R_E_C_N_O_ IS NOT NULL
            THEN 1 ELSE 0 END AS is_return
  FROM SD2010 D2 WITH (NOLOCK)
{tes_apply}
 INNER JOIN SB1010 P WITH (NOLOCK)
         ON P.B1_COD = D2.D2_COD
        AND P.D_E_L_E_T_ = ' '
  LEFT JOIN SF2010 DEV WITH (NOLOCK)
         ON DEV.F2_FILIAL = D2.D2_FILIAL
        AND DEV.F2_DOC = D2.D2_DOC
        AND DEV.F2_SERIE = D2.D2_SERIE
        AND DEV.F2_CLIENTE = D2.D2_CLIENTE
        AND DEV.F2_LOJA = D2.D2_LOJA
        AND DEV.D_E_L_E_T_ = ' '
 WHERE D2.D_E_L_E_T_ = ' '
   AND TES.estoque = 'S'
   AND D2.D2_FILIAL IN ({branch_placeholders})
   AND D2.D2_EMISSAO BETWEEN ? AND ?
   AND D2.D2_ORIGLAN <> 'LF'
{filters}
"""

_SD3_PART = """
SELECT 'SD3' AS source_table,
       D3.R_E_C_N_O_ AS movement_id,
       RTRIM(D3.D3_FILIAL) AS branch_code,
       RTRIM(D3.D3_LOCAL) AS warehouse,
       RTRIM(D3.D3_COD) AS product_code,
       RTRIM(P.B1_DESC) AS description,
       RTRIM(P.B1_TIPO) AS product_type,
       RTRIM(P.B1_GRUPO) AS product_group,
       RTRIM(P.B1_UM) AS unit,
       RTRIM(D3.D3_DOC) AS document,
       '' AS series,
       RTRIM(D3.D3_EMISSAO) AS movement_date,
       RTRIM(D3.D3_NUMSEQ) AS sequence_number,
       RTRIM(D3.D3_TM) AS tm,
       RTRIM(D3.D3_CF) AS cf,
       '' AS partner_code,
       '' AS partner_store,
       '' AS order_number,
       '' AS document_type,
       RTRIM(D3.D3_PROJPMS) AS project_code,
       RTRIM(D3.D3_OP) AS production_order,
       RTRIM(D3.D3_CC) AS cost_center,
       CAST(D3.D3_QUANT AS DECIMAL(30,9)) AS quantity,
       CAST(D3.D3_CUSTO1 AS DECIMAL(30,9)) AS total_cost,
       0 AS is_return
  FROM SD3010 D3 WITH (NOLOCK)
 INNER JOIN SB1010 P WITH (NOLOCK)
         ON P.B1_COD = D3.D3_COD
        AND P.D_E_L_E_T_ = ' '
 WHERE D3.D_E_L_E_T_ = ' '
   AND D3.D3_FILIAL IN ({branch_placeholders})
   AND D3.D3_EMISSAO BETWEEN ? AND ?
{sd3_predicates}
{filters}
"""

# SD3 producer predicates (matr910_dlp.prx L407-421 / L507-524): the
# estorno exclusion applies when MV_D3ESTOR='N' (live value: 'N'); the
# service clause keeps service rows only when TM<='500' or the movement
# lands on the CQ warehouse (MV_CQ, live value: '98').
_SD3_ESTORNO_CLAUSE = "   AND D3.D3_ESTORNO <> 'S'"
_SD3_SERVICE_CLAUSE = """
   AND ( RTRIM(D3.D3_SERVIC) = ''
      OR (RTRIM(D3.D3_SERVIC) <> '' AND D3.D3_TM <= '500')
      OR (RTRIM(D3.D3_SERVIC) <> '' AND D3.D3_TM > '500'
          AND D3.D3_LOCAL = ?) )
"""
_SD3_INVENT_CLAUSE = "   AND D3.D3_DOC = 'INVENT'"

# Opening balance — SB9 closing of the PREVIOUS month, same grain
# (branch, warehouse, product) the movements partition by.
_OPENING_BALANCE_SQL = """
SELECT RTRIM(S.B9_FILIAL) AS branch_code,
       RTRIM(S.B9_LOCAL) AS warehouse,
       RTRIM(S.B9_COD)   AS product_code,
       CAST(SUM(S.B9_QINI)  AS DECIMAL(30,9)) AS opening_quantity,
       CAST(SUM(S.B9_VINI1) AS DECIMAL(30,9)) AS opening_value
  FROM SB9010 S WITH (NOLOCK)
 WHERE S.D_E_L_E_T_ = ''
   AND S.B9_DATA = ?
   AND S.B9_FILIAL IN ({branch_placeholders})
   AND S.B9_COD IN ({product_placeholders})
{warehouse_filter}
 GROUP BY S.B9_FILIAL, S.B9_LOCAL, S.B9_COD
"""

# Table-specific TTAT logs (SD2010_TTAT_LOG / SD3010_TTAT_LOG): the as-of
# cost is the COLD value of the FIRST change logged after the period
# boundary — that is the value the field carried at the boundary.
_TTAT_HISTORY_SQL = """
SELECT TTAT_RECNO, TTAT_COLD, TTAT_DTIME
  FROM {log_table} WITH (NOLOCK)
 WHERE TTAT_FIELD = ?
   AND TTAT_DTIME > ?
   AND TTAT_RECNO IN ({recno_placeholders})
 ORDER BY TTAT_RECNO, TTAT_DTIME
"""

_SX6_PARAM_SQL = """
SELECT TOP 1 RTRIM(X6_CONTEUD) AS param_value
  FROM SX6010 WITH (NOLOCK)
 WHERE D_E_L_E_T_ = ''
   AND X6_VAR = ?
 ORDER BY CASE WHEN RTRIM(X6_FIL) = '' THEN 1 ELSE 0 END
"""


def _in_placeholders(values: tuple[str, ...]) -> str:
    return ", ".join("?" for _ in values)


def _movement_filters(
    *,
    product_code: str | None,
    product_type: str | None,
    imported_product: str | None,
    alias: str,
) -> tuple[str, list[Any]]:
    """Shared movement predicates — warehouse/product/type/import."""
    filters: list[str] = []
    params: list[Any] = []
    if product_code:
        filters.append(f"   AND RTRIM({alias}_COD) = ?")
        params.append(product_code)
    if product_type:
        filters.append("   AND RTRIM(P.B1_TIPO) = ?")
        params.append(product_type)
    if imported_product:
        filters.append("   AND P.B1_COD <> ?")
        params.append(imported_product)
    return "\n".join(filters), params


def _warehouse_filter(
    *, warehouses: tuple[str, ...] | None, column: str
) -> tuple[str, list[Any]]:
    if not warehouses:
        return "", []
    return (
        f"   AND {column} IN ({_in_placeholders(warehouses)})",
        list(warehouses),
    )


def build_movements_query(
    *,
    period_start: str,
    period_end: str,
    branches: tuple[str, ...],
    warehouses: tuple[str, ...] | None,
    product_code: str | None,
    product_type: str | None,
    document_kind: str,
    imported_product: str | None,
    exclude_estorno: bool,
    cq_warehouse: str,
) -> tuple[str, list[Any]]:
    """Full filtered movement union — one engine, all presentations.

    Returns every movement line of the authorized universe (no SQL
    paging): the running-balance chain and the global aggregates are
    computed over the whole set at the data owner. Sorting is fixed —
    deterministic by (branch, product, warehouse, date, seq, recno).
    """
    branch_ph = _in_placeholders(branches)
    parts: list[str] = []
    params: list[Any] = []

    invent_only = document_kind == "invent"

    if not invent_only:
        for part, table, filial_col, local_col, cod_col in (
            (_SD1_PART, "SD1", "D1.D1_FILIAL", "D1.D1_LOCAL", "D1.D1_COD"),
            (_SD2_PART, "SD2", "D2.D2_FILIAL", "D2.D2_LOCAL", "D2.D2_COD"),
        ):
            tes_apply = _TES_APPLY.format(
                tes_column={"SD1": "D1.D1_TES", "SD2": "D2.D2_TES"}[table],
                filial_column=filial_col,
            )
            filters, filter_params = _movement_filters(
                product_code=product_code,
                product_type=product_type,
                imported_product=imported_product,
                alias={"SD1": "D1.D1", "SD2": "D2.D2"}[table],
            )
            wh_clause, wh_params = _warehouse_filter(
                warehouses=warehouses, column=local_col
            )
            if wh_clause:
                filters = wh_clause + "\n" + filters if filters else wh_clause
            sql = part.format(
                tes_apply=tes_apply,
                branch_placeholders=branch_ph,
                filters=filters,
            )
            parts.append(sql)
            params.extend(
                [
                    *branches,
                    period_start,
                    period_end,
                    *wh_params,
                    *filter_params,
                ]
            )

    sd3_predicates = ""
    sd3_pred_params: list[Any] = []
    if exclude_estorno:
        sd3_predicates += _SD3_ESTORNO_CLAUSE
    if cq_warehouse:
        sd3_predicates += _SD3_SERVICE_CLAUSE
        sd3_pred_params.append(cq_warehouse)
    if invent_only:
        sd3_predicates += _SD3_INVENT_CLAUSE

    filters, filter_params = _movement_filters(
        product_code=product_code,
        product_type=product_type,
        imported_product=imported_product,
        alias="D3.D3",
    )
    wh_clause, wh_params = _warehouse_filter(
        warehouses=warehouses, column="D3.D3_LOCAL"
    )
    if wh_clause:
        filters = wh_clause + "\n" + filters if filters else wh_clause
    sd3_sql = _SD3_PART.format(
        branch_placeholders=branch_ph,
        sd3_predicates=sd3_predicates,
        filters=filters,
    )
    parts.append(sd3_sql)
    params.extend(
        [
            *branches,
            period_start,
            period_end,
            *sd3_pred_params,
            *wh_params,
            *filter_params,
        ]
    )

    union = "\nUNION ALL\n".join(parts)
    return (
        "SELECT * FROM (\n" + union + "\n) MOV\n"
        "ORDER BY branch_code, product_code, warehouse, movement_date,\n"
        "         sequence_number, movement_id\n",
        params,
    )


def build_opening_balance_query(
    *,
    snapshot_date: str,
    branches: tuple[str, ...],
    product_codes: tuple[str, ...],
    warehouses: tuple[str, ...] | None,
) -> tuple[str, list[Any]]:
    """SB9 opening positions at the previous month-end, restricted to
    the products that actually moved (MATR910 population rule)."""
    wh_clause, wh_params = _warehouse_filter(
        warehouses=warehouses, column="S.B9_LOCAL"
    )
    sql = _OPENING_BALANCE_SQL.format(
        branch_placeholders=_in_placeholders(branches),
        product_placeholders=_in_placeholders(product_codes),
        warehouse_filter=wh_clause,
    )
    return sql, [snapshot_date, *branches, *product_codes, *wh_params]


# TTAT per-table log map — only the tables whose cost field drives the
# printed CUSTO column (SD1 has no cost TTAT log in this environment).
_TTAT_LOG_TABLES = {
    "SD2": ("SD2010_TTAT_LOG", "D2_CUSTO1"),
    "SD3": ("SD3010_TTAT_LOG", "D3_CUSTO1"),
}


def ttat_log_table(source_table: str) -> tuple[str, str] | None:
    return _TTAT_LOG_TABLES.get(source_table)


def build_ttat_history_query(
    *,
    log_table: str,
    field_name: str,
    boundary: str,
    recnos: tuple[int, ...],
) -> tuple[str, list[Any]]:
    sql = _TTAT_HISTORY_SQL.format(
        log_table=log_table,
        recno_placeholders=", ".join("?" for _ in recnos),
    )
    return sql, [field_name, boundary, *recnos]


def build_sx6_param_query(param_name: str) -> tuple[str, list[Any]]:
    return _SX6_PARAM_SQL, [param_name]
