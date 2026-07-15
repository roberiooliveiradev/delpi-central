"""SQL builders — Apontamento de Produção (SH6010 → SH1010 → SHB010).

Validado na Fase 0 (jul/2026): docs/12-roadmap-e-evolucao/production-appointments/
"""

from __future__ import annotations

from app.domain.production.production_appointments.production_appointments_scope import (
    CT_INSPECAO_NOME_SQL_LIKE,
)

_CT_JOIN = """
INNER JOIN SH1010 SH1 WITH (NOLOCK)
    ON SH1.H1_FILIAL = SH6.H6_FILIAL
   AND SH1.H1_CODIGO = SH6.H6_RECURSO
   AND SH1.D_E_L_E_T_ = ' '
INNER JOIN SHB010 HB WITH (NOLOCK)
    ON HB.HB_FILIAL = SH6.H6_FILIAL
   AND HB.HB_COD = SH1.H1_CTRAB
   AND HB.D_E_L_E_T_ = ' '
"""

_PRODUCT_JOIN = """
LEFT JOIN SB1010 SB1 WITH (NOLOCK)
    ON SB1.B1_COD = SH6.H6_PRODUTO
   AND SB1.D_E_L_E_T_ = ' '
"""

_IS_FINAL_INSPECTION_EXPR = (
    f"CASE WHEN UPPER(HB.HB_NOME) LIKE '{CT_INSPECAO_NOME_SQL_LIKE}' THEN 1 ELSE 0 END"
)

_BASE_FROM = f"""
FROM SH6010 SH6 WITH (NOLOCK)
{_CT_JOIN}
{_PRODUCT_JOIN}
"""


def build_appointments_where(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    work_center: str | None = None,
    op: str | None = None,
    product: str | None = None,
) -> tuple[str, list]:
    clauses = [
        "SH6.D_E_L_E_T_ = ' '",
        "SH6.H6_TIPO = 'P'",
        "SH6.H6_OP <> ''",
        "SH6.H6_RECURSO <> ''",
        "LTRIM(RTRIM(SH6.H6_FILIAL)) = ?",
        "SH6.H6_DTAPONT >= ?",
        "SH6.H6_DTAPONT < ?",
    ]
    params: list = [branch, date_start, date_end_exclusive]

    if work_center:
        clauses.append("LTRIM(RTRIM(SH1.H1_CTRAB)) = ?")
        params.append(work_center.strip())
    if op:
        clauses.append("LTRIM(RTRIM(SH6.H6_OP)) = ?")
        params.append(op.strip())
    if product:
        clauses.append("LTRIM(RTRIM(SH6.H6_PRODUTO)) = ?")
        params.append(product.strip())

    return " AND ".join(clauses), params


def build_work_centers_catalog_query(*, branch: str) -> tuple[str, tuple]:
    sql = f"""
    SELECT
        LTRIM(RTRIM(HB.HB_FILIAL)) AS branch,
        LTRIM(RTRIM(HB.HB_COD)) AS work_center,
        LTRIM(RTRIM(HB.HB_NOME)) AS name,
        {_IS_FINAL_INSPECTION_EXPR} AS is_final_inspection
    FROM SHB010 HB WITH (NOLOCK)
    WHERE HB.D_E_L_E_T_ = ' '
      AND LTRIM(RTRIM(HB.HB_FILIAL)) = ?
    ORDER BY LTRIM(RTRIM(HB.HB_COD))
    """
    return sql, (branch,)


def build_appointments_list_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    offset: int,
    page_size: int,
    work_center: str | None = None,
    op: str | None = None,
    product: str | None = None,
) -> tuple[str, tuple]:
    where, params = build_appointments_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
        work_center=work_center,
        op=op,
        product=product,
    )
    sql = f"""
    SELECT
        LTRIM(RTRIM(SH6.H6_FILIAL)) AS branch,
        LTRIM(RTRIM(SH6.H6_OP)) AS production_order,
        LTRIM(RTRIM(SH6.H6_PRODUTO)) AS product,
        LTRIM(RTRIM(SB1.B1_TIPO)) AS product_type,
        LTRIM(RTRIM(SB1.B1_DESC)) AS product_description,
        LTRIM(RTRIM(SH1.H1_CTRAB)) AS work_center,
        LTRIM(RTRIM(HB.HB_NOME)) AS work_center_name,
        {_IS_FINAL_INSPECTION_EXPR} AS is_final_inspection,
        LTRIM(RTRIM(SH6.H6_OPERAC)) AS operation,
        LTRIM(RTRIM(SH6.H6_RECURSO)) AS resource,
        CAST(SH6.H6_QTDPROD AS FLOAT) AS qty_produced,
        CAST(SH6.H6_QTDPERD AS FLOAT) AS qty_lost,
        LTRIM(RTRIM(SH6.H6_DTAPONT)) AS appointment_date,
        SH6.R_E_C_N_O_ AS appointment_id
    {_BASE_FROM}
    WHERE {where}
    ORDER BY SH6.H6_DTAPONT DESC, SH6.R_E_C_N_O_ DESC
    OFFSET {int(offset)} ROWS FETCH NEXT {int(page_size)} ROWS ONLY
    """
    return sql, tuple(params)


def build_appointments_count_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    work_center: str | None = None,
    op: str | None = None,
    product: str | None = None,
) -> tuple[str, tuple]:
    where, params = build_appointments_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
        work_center=work_center,
        op=op,
        product=product,
    )
    sql = f"""
    SELECT COUNT(*) AS total
    {_BASE_FROM}
    WHERE {where}
    """
    return sql, tuple(params)


def build_summary_by_ct_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    work_center: str | None = None,
    op: str | None = None,
    product: str | None = None,
) -> tuple[str, tuple]:
    where, params = build_appointments_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
        work_center=work_center,
        op=op,
        product=product,
    )
    sql = f"""
    SELECT
        LTRIM(RTRIM(SH1.H1_CTRAB)) AS work_center,
        LTRIM(RTRIM(HB.HB_NOME)) AS work_center_name,
        {_IS_FINAL_INSPECTION_EXPR} AS is_final_inspection,
        COUNT(*) AS appointment_count,
        SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) AS qty_produced,
        SUM(CAST(SH6.H6_QTDPERD AS FLOAT)) AS qty_lost,
        COUNT(DISTINCT LTRIM(RTRIM(SH6.H6_OP))) AS op_count
    {_BASE_FROM}
    WHERE {where}
    GROUP BY SH1.H1_CTRAB, HB.HB_NOME
    ORDER BY qty_produced DESC
    """
    return sql, tuple(params)


def build_summary_totals_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    work_center: str | None = None,
    op: str | None = None,
    product: str | None = None,
) -> tuple[str, tuple]:
    where, params = build_appointments_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
        work_center=work_center,
        op=op,
        product=product,
    )
    sql = f"""
    SELECT
        COUNT(*) AS appointment_count,
        SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) AS qty_produced,
        SUM(CAST(SH6.H6_QTDPERD AS FLOAT)) AS qty_lost,
        COUNT(DISTINCT LTRIM(RTRIM(SH6.H6_OP))) AS op_count,
        COUNT(DISTINCT LTRIM(RTRIM(SH1.H1_CTRAB))) AS work_center_count
    {_BASE_FROM}
    WHERE {where}
    """
    return sql, tuple(params)


def build_series_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    group_by: str = "day",
    work_center: str | None = None,
    op: str | None = None,
    product: str | None = None,
) -> tuple[str, tuple]:
    where, params = build_appointments_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
        work_center=work_center,
        op=op,
        product=product,
    )
    if group_by == "day_work_center":
        sql = f"""
        SELECT
            LTRIM(RTRIM(SH6.H6_DTAPONT)) AS appointment_date,
            LTRIM(RTRIM(SH1.H1_CTRAB)) AS work_center,
            LTRIM(RTRIM(HB.HB_NOME)) AS work_center_name,
            {_IS_FINAL_INSPECTION_EXPR} AS is_final_inspection,
            COUNT(*) AS appointment_count,
            SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) AS qty_produced,
            SUM(CAST(SH6.H6_QTDPERD AS FLOAT)) AS qty_lost
        {_BASE_FROM}
        WHERE {where}
        GROUP BY SH6.H6_DTAPONT, SH1.H1_CTRAB, HB.HB_NOME
        ORDER BY SH6.H6_DTAPONT, SH1.H1_CTRAB
        """
    else:
        sql = f"""
        SELECT
            LTRIM(RTRIM(SH6.H6_DTAPONT)) AS appointment_date,
            COUNT(*) AS appointment_count,
            SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) AS qty_produced,
            SUM(CAST(SH6.H6_QTDPERD AS FLOAT)) AS qty_lost
        {_BASE_FROM}
        WHERE {where}
        GROUP BY SH6.H6_DTAPONT
        ORDER BY SH6.H6_DTAPONT
        """
    return sql, tuple(params)


def build_by_op_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    offset: int,
    page_size: int,
    work_center: str | None = None,
    op: str | None = None,
    product: str | None = None,
) -> tuple[str, tuple]:
    where, params = build_appointments_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
        work_center=work_center,
        op=op,
        product=product,
    )
    sql = f"""
    SELECT
        LTRIM(RTRIM(SH6.H6_OP)) AS production_order,
        LTRIM(RTRIM(SH6.H6_PRODUTO)) AS product,
        LTRIM(RTRIM(SB1.B1_TIPO)) AS product_type,
        LTRIM(RTRIM(SB1.B1_DESC)) AS product_description,
        COUNT(*) AS appointment_count,
        COUNT(DISTINCT LTRIM(RTRIM(SH1.H1_CTRAB))) AS work_center_count,
        SUM(CAST(SH6.H6_QTDPROD AS FLOAT)) AS qty_produced,
        SUM(CAST(SH6.H6_QTDPERD AS FLOAT)) AS qty_lost,
        MIN(LTRIM(RTRIM(SH6.H6_DTAPONT))) AS first_date,
        MAX(LTRIM(RTRIM(SH6.H6_DTAPONT))) AS last_date
    {_BASE_FROM}
    WHERE {where}
    GROUP BY SH6.H6_OP, SH6.H6_PRODUTO, SB1.B1_TIPO, SB1.B1_DESC
    ORDER BY qty_produced DESC, SH6.H6_OP
    OFFSET {int(offset)} ROWS FETCH NEXT {int(page_size)} ROWS ONLY
    """
    return sql, tuple(params)


def build_by_op_count_query(
    *,
    date_start: str,
    date_end_exclusive: str,
    branch: str,
    work_center: str | None = None,
    op: str | None = None,
    product: str | None = None,
) -> tuple[str, tuple]:
    where, params = build_appointments_where(
        date_start=date_start,
        date_end_exclusive=date_end_exclusive,
        branch=branch,
        work_center=work_center,
        op=op,
        product=product,
    )
    sql = f"""
    SELECT COUNT(*) AS total
    FROM (
        SELECT SH6.H6_OP, SH6.H6_PRODUTO
        {_BASE_FROM}
        WHERE {where}
        GROUP BY SH6.H6_OP, SH6.H6_PRODUTO
    ) G
    """
    return sql, tuple(params)
