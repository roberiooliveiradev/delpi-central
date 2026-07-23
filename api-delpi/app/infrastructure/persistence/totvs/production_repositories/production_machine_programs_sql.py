"""SQL — ranking de intermediários (PI) apontados para programas de máquina.

Fonte: SH6010 (apontamentos) + SB1 (tipo PI) + SC2 (PA via OP mãe 01001) + SG2 (CT op 01).
"""

from __future__ import annotations

from app.domain.services.supplies.safety_stock_stock_projection_service import (
    FINISHED_PRODUCTION_ORDER_SUFFIX,
)

_FINISHED_OP_EXPR = (
    f"LEFT(RTRIM(A.production_order), 6) + '{FINISHED_PRODUCTION_ORDER_SUFFIX}'"
)

# CTs de corte que não entram no ranking de programas de máquina.
EXCLUDED_CUTTING_WORK_CENTERS: tuple[str, ...] = ("CT-02A",)


def _excluded_ct_sql_literals() -> str:
    return ", ".join(f"'{code}'" for code in EXCLUDED_CUTTING_WORK_CENTERS)


def build_top_intermediates_sql(
    *,
    search: str | None,
    offset: int,
    page_size: int,
) -> tuple[str, str]:
    """Retorna (sql_items, sql_count).

    Params (mesma ordem em items e count):
      branch, date_start, date_end_exclusive,  -- appointments
      branch,                                  -- SC2 PA
      branch,                                  -- SG2 CT
      branch,                                  -- SC2 OP aberta
      [search, search]                         -- opcional
    """
    search_filter = ""
    if search:
        search_filter = """
          AND (
            AGG.intermediate_code LIKE ?
            OR COALESCE(PA.finished_product_code, '') LIKE ?
          )
        """

    excluded_cts = _excluded_ct_sql_literals()
    ct_exclusion = f"""
          AND COALESCE(SG2.cutting_work_center, '') NOT IN ({excluded_cts})
    """

    ranked_cte = f"""
    WITH appointments AS (
        SELECT
            LTRIM(RTRIM(SH6.H6_PRODUTO)) AS intermediate_code,
            LTRIM(RTRIM(SH6.H6_OP)) AS production_order,
            CAST(
                REPLACE(LTRIM(RTRIM(SH6.H6_QTDPROD)), ',', '.') AS FLOAT
            ) AS qty_produced
        FROM SH6010 SH6 WITH (NOLOCK)
        INNER JOIN SB1010 SB1 WITH (NOLOCK)
            ON SB1.B1_COD = SH6.H6_PRODUTO
           AND SB1.D_E_L_E_T_ = ''
           AND LTRIM(RTRIM(SB1.B1_TIPO)) = 'PI'
        WHERE SH6.D_E_L_E_T_ = ''
          AND SH6.H6_TIPO = 'P'
          AND SH6.H6_FILIAL = ?
          AND SH6.H6_DTAPONT >= ?
          AND SH6.H6_DTAPONT < ?
          AND LTRIM(RTRIM(SH6.H6_OP)) <> ''
          AND LTRIM(RTRIM(SH6.H6_PRODUTO)) <> ''
          AND LTRIM(RTRIM(SH6.H6_PRODUTO)) LIKE '5%'
    ),
    with_pa AS (
        SELECT
            A.intermediate_code,
            A.qty_produced,
            A.production_order,
            RTRIM(COALESCE(FP.C2_PRODUTO, '')) AS finished_product_code
        FROM appointments A
        LEFT JOIN SC2010 FP WITH (NOLOCK)
            ON FP.D_E_L_E_T_ = ''
           AND FP.C2_FILIAL = ?
           AND LEN(RTRIM(A.production_order)) >= 6
           AND RTRIM(LTRIM(FP.C2_OP)) = {_FINISHED_OP_EXPR}
    ),
    agg AS (
        SELECT
            intermediate_code,
            SUM(qty_produced) AS qty_produced,
            COUNT_BIG(*) AS appointment_count
        FROM with_pa
        GROUP BY intermediate_code
    ),
    pa_counts AS (
        SELECT
            intermediate_code,
            finished_product_code,
            COUNT_BIG(*) AS cnt
        FROM with_pa
        WHERE finished_product_code <> ''
        GROUP BY intermediate_code, finished_product_code
    ),
    pa_mode AS (
        SELECT
            intermediate_code,
            finished_product_code,
            ROW_NUMBER() OVER (
                PARTITION BY intermediate_code
                ORDER BY cnt DESC, finished_product_code ASC
            ) AS rn
        FROM pa_counts
    )
    """

    from_join = f"""
    FROM agg AGG
    LEFT JOIN pa_mode PA
        ON PA.intermediate_code = AGG.intermediate_code
       AND PA.rn = 1
    OUTER APPLY (
        SELECT TOP 1
            RTRIM(COALESCE(SB1.B1_DESC, '')) AS intermediate_description
        FROM SB1010 SB1 WITH (NOLOCK)
        WHERE SB1.B1_COD = AGG.intermediate_code
          AND SB1.D_E_L_E_T_ = ''
        ORDER BY SB1.B1_COD
    ) SB1
    OUTER APPLY (
        SELECT TOP 1
            RTRIM(COALESCE(SG2.G2_CTRAB, '')) AS cutting_work_center
        FROM SG2010 SG2 WITH (NOLOCK)
        WHERE SG2.D_E_L_E_T_ = ''
          AND SG2.G2_FILIAL = ?
          AND SG2.G2_PRODUTO = AGG.intermediate_code
          AND RTRIM(LTRIM(SG2.G2_OPERAC)) = '01'
        ORDER BY SG2.G2_CODIGO, SG2.G2_CTRAB
    ) SG2
    OUTER APPLY (
        SELECT TOP 1 1 AS has_open
        FROM SC2010 OP WITH (NOLOCK)
        WHERE OP.D_E_L_E_T_ = ''
          AND OP.C2_FILIAL = ?
          AND RTRIM(LTRIM(OP.C2_PRODUTO)) = AGG.intermediate_code
          AND OP.C2_QUANT > OP.C2_QUJE
          AND RTRIM(COALESCE(OP.C2_DATRF, '')) = ''
    ) OPEN_OP
    WHERE 1 = 1
    {ct_exclusion}
    {search_filter}
    """

    select_cols = """
        AGG.intermediate_code AS intermediate_code,
        COALESCE(SB1.intermediate_description, '') AS intermediate_description,
        RTRIM(COALESCE(PA.finished_product_code, '')) AS finished_product_code,
        COALESCE(SG2.cutting_work_center, '') AS cutting_work_center,
        CASE WHEN OPEN_OP.has_open IS NOT NULL THEN 1 ELSE 0 END
            AS has_open_production_order,
        AGG.qty_produced AS qty_produced,
        CAST(AGG.appointment_count AS INT) AS appointment_count
    """

    sql_items = f"""
    {ranked_cte}
    SELECT
    {select_cols}
    {from_join}
    ORDER BY AGG.qty_produced DESC, AGG.intermediate_code ASC
    OFFSET {int(offset)} ROWS FETCH NEXT {int(page_size)} ROWS ONLY
    """

    sql_count = f"""
    {ranked_cte}
    SELECT COUNT_BIG(*) AS total
    {from_join}
    """

    return sql_items, sql_count
