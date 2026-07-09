from __future__ import annotations

from typing import Optional, Tuple

from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

_SALES_ORDER_OTD_ON_TIME_CASE = """
    CASE
        WHEN RTRIM(ISNULL(CAST(C6_DATFAT AS VARCHAR(20)), '')) <> ''
            THEN CASE WHEN C6_DATFAT <= C6_ENTREG THEN 1 ELSE 0 END
        WHEN COALESCE(?, CONVERT(VARCHAR(8), GETDATE(), 112)) > C6_ENTREG THEN 0
        ELSE 1
    END
"""


def build_sales_order_otd_filters(
    *,
    branch: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    customer_segment: Optional[str],
) -> Tuple[str, tuple]:
    from app.domain.services.commercial_customer_segment_service import (
        CommercialCustomerSegmentService,
    )

    qb = QueryBuilder()
    qb.raw("C6.D_E_L_E_T_ = ''")
    qb.raw("C5.D_E_L_E_T_ = ''")
    qb.raw("C6.C6_QTDVEN > 0")
    qb.raw("C6.C6_ENTREG IS NOT NULL")
    qb.raw("RTRIM(CAST(C6.C6_ENTREG AS VARCHAR(20))) <> ''")
    qb.raw("(C6.C6_BLOQUEI IS NULL OR RTRIM(C6.C6_BLOQUEI) = '')")
    qb.raw("(C6.C6_BLQ IS NULL OR RTRIM(C6.C6_BLQ) = '')")

    if branch:
        qb.eq("C6.C6_FILIAL", branch)

    qb.date_range("C6.C6_ENTREG", start_date, end_date)

    CommercialCustomerSegmentService.apply_segment_to_query_builder(
        qb,
        "C5.C5_CLIENTE",
        customer_segment,
    )

    return qb.build()


def build_sales_order_otd_sql(
    *,
    where_clause: str,
    reference_end_date: Optional[str],
) -> Tuple[str, tuple]:
    reference_date = QueryBuilder().convert_date_to_protheus(reference_end_date)

    sql = f"""
        WITH linhas_elegiveis AS (
            SELECT DISTINCT
                C6.C6_FILIAL,
                C6.C6_NUM,
                C6.C6_ITEM,
                C6.C6_ENTREG,
                C6.C6_DATFAT
            FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
                ON  C5.C5_FILIAL = C6.C6_FILIAL
                AND C5.C5_NUM = C6.C6_NUM
            WHERE {where_clause}
        )
        SELECT
            COUNT(*) AS total_lines,
            SUM({_SALES_ORDER_OTD_ON_TIME_CASE}) AS on_time_lines,
            SUM(CASE WHEN ({_SALES_ORDER_OTD_ON_TIME_CASE}) = 0 THEN 1 ELSE 0 END)
                AS late_lines,
            CAST(
                CASE
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE SUM({_SALES_ORDER_OTD_ON_TIME_CASE}) * 100.0 / COUNT(*)
                END
            AS DECIMAL(10, 2)) AS sales_order_otd_pct
        FROM linhas_elegiveis
    """

    return sql, (reference_date, reference_date, reference_date)
