from __future__ import annotations

from typing import Optional, Tuple

from app.application.dto.commercial.get_sales_order_otd_panel_request import (
    GetSalesOrderOtdPanelRequest,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

_SALES_ORDER_OTD_ON_TIME_CASE = """
    CASE
        WHEN RTRIM(ISNULL(CAST(C6_DATFAT AS VARCHAR(20)), '')) <> ''
            THEN CASE WHEN C6_DATFAT <= C6_ENTREG THEN 1 ELSE 0 END
        WHEN COALESCE(?, CONVERT(VARCHAR(8), GETDATE(), 112)) > C6_ENTREG THEN 0
        ELSE 1
    END
"""

# UM da linha do pedido (C6); cadastro SB1 só como fallback — sem conversão.
_LINE_UNIT_SQL = """
            COALESCE(
                NULLIF(RTRIM(LTRIM(C6.C6_UM)), ''),
                RTRIM(LTRIM(B1.B1_UM)),
                ''
            )
""".strip()

_SB1_JOIN_SQL = """
            LEFT JOIN SB1010 B1 WITH (NOLOCK)
                ON  B1.B1_COD = C6.C6_PRODUTO
                AND B1.D_E_L_E_T_ = ''
""".strip()

_AGG_UNIT_SELECT_SQL = """
            CASE
                WHEN COUNT(*) = 0 THEN NULL
                WHEN COUNT(DISTINCT unit) = 1 THEN MAX(unit)
                ELSE NULL
            END AS unit,
            CASE
                WHEN COUNT(*) > 0 AND COUNT(DISTINCT unit) > 1 THEN 1
                ELSE 0
            END AS mixed_units
""".strip()

_LIST_LINES_CTE = """
    LINHAS_ELEGIVEIS AS (
        SELECT DISTINCT
            C6.C6_FILIAL AS branch,
            RTRIM(LTRIM(C6.C6_NUM)) AS order_number,
            RTRIM(LTRIM(C6.C6_ITEM)) AS line_item,
            RTRIM(LTRIM(C6.C6_PRODUTO)) AS product_code,
            RTRIM(LTRIM(B1.B1_DESC)) AS product_description,
            {_line_unit} AS unit,
            RTRIM(LTRIM(C5.C5_CLIENTE)) AS customer_code,
            RTRIM(LTRIM(C5.C5_LOJACLI)) AS customer_store,
            COALESCE(
                NULLIF(RTRIM(LTRIM(SA1.A1_NREDUZ)), ''),
                RTRIM(LTRIM(SA1.A1_NOME))
            ) AS customer_name,
            RTRIM(LTRIM(SA1.A1_NREDUZ)) AS customer_short_name,
            C6.C6_QTDVEN AS qty_sold,
            C6.C6_QTDENT AS qty_delivered,
            CONVERT(VARCHAR(10), CONVERT(DATE, C6.C6_ENTREG, 112), 23) AS promised_date,
            CASE
                WHEN RTRIM(ISNULL(CAST(C6.C6_DATFAT AS VARCHAR(20)), '')) <> ''
                THEN CONVERT(VARCHAR(10), CONVERT(DATE, C6.C6_DATFAT, 112), 23)
                ELSE NULL
            END AS invoice_date,
            CASE
                WHEN RTRIM(ISNULL(CAST(C6.C6_DATFAT AS VARCHAR(20)), '')) <> ''
                THEN 1
                ELSE 0
            END AS is_invoiced,
            {_on_time_case} AS is_on_time,
            CASE
                WHEN {_on_time_case} = 1 THEN 'on_time'
                ELSE 'late'
            END AS status,
            DATEDIFF(
                DAY,
                CONVERT(DATE, C6.C6_ENTREG, 112),
                CONVERT(
                    DATE,
                    CASE
                        WHEN RTRIM(ISNULL(CAST(C6.C6_DATFAT AS VARCHAR(20)), '')) <> ''
                        THEN C6.C6_DATFAT
                        ELSE COALESCE(?, CONVERT(VARCHAR(8), GETDATE(), 112))
                    END,
                    112
                )
            ) AS days_diff
        FROM SC6010 C6 WITH (NOLOCK)
        INNER JOIN SC5010 C5 WITH (NOLOCK)
            ON  C5.C5_FILIAL = C6.C6_FILIAL
            AND C5.C5_NUM = C6.C6_NUM
        LEFT JOIN SB1010 B1 WITH (NOLOCK)
            ON  B1.B1_COD = C6.C6_PRODUTO
            AND B1.D_E_L_E_T_ = ''
        LEFT JOIN SA1010 SA1 WITH (NOLOCK)
            ON  SA1.A1_COD = C5.C5_CLIENTE
            AND SA1.A1_LOJA = C5.C5_LOJACLI
            AND SA1.D_E_L_E_T_ = ''
        WHERE {where_clause}
    )
"""


def build_sales_order_otd_filters(
    *,
    branch: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    customer_segment: Optional[str],
    customer_codes: Optional[list[str]] = None,
    customer_code_stores: Optional[list[tuple[str, str]]] = None,
    customer_names: Optional[list[str]] = None,
    exclude_customer_codes: Optional[list[str]] = None,
    exclude_customer_names: Optional[list[str]] = None,
) -> Tuple[str, tuple]:
    from app.domain.services.commercial_analysis_filter_service import (
        CommercialAnalysisFilterService,
    )

    qb = QueryBuilder()
    qb.raw("C6.D_E_L_E_T_ = ''")
    qb.raw("C5.D_E_L_E_T_ = ''")
    qb.raw("C6.C6_QTDVEN > 0")
    qb.raw("C6.C6_ENTREG IS NOT NULL")
    qb.raw("RTRIM(CAST(C6.C6_ENTREG AS VARCHAR(20))) <> ''")
    qb.raw("(C6.C6_BLOQUEI IS NULL OR RTRIM(C6.C6_BLOQUEI) = '')")
    qb.raw("(C6.C6_BLQ IS NULL OR RTRIM(C6.C6_BLQ) = '')")

    # TV wire envia branch=all para «Todas as filiais»; não filtrar literal 'all'.
    from app.domain.totvs.protheus_branches import optional_concrete_branch

    concrete_branch = optional_concrete_branch(branch)
    if concrete_branch:
        qb.eq("C6.C6_FILIAL", concrete_branch)

    qb.date_range("C6.C6_ENTREG", start_date, end_date)

    CommercialAnalysisFilterService.apply_to_query_builder(
        qb,
        customer_code_column="C5.C5_CLIENTE",
        customer_name_column="SA1.A1_NOME",
        customer_store_column="C5.C5_LOJACLI",
        customer_segment=customer_segment,
        customer_codes=customer_codes,
        customer_code_stores=customer_code_stores,
        customer_names=customer_names,
        exclude_customer_codes=exclude_customer_codes,
        exclude_customer_names=exclude_customer_names,
    )

    return qb.build()


def _reference_date_param(reference_end_date: Optional[str]) -> Optional[str]:
    return QueryBuilder().convert_date_to_protheus(reference_end_date)


def _list_cte_sql(*, where_clause: str) -> str:
    on_time_case = _SALES_ORDER_OTD_ON_TIME_CASE.replace("C6_DATFAT", "C6.C6_DATFAT").replace(
        "C6_ENTREG", "C6.C6_ENTREG"
    )
    return _LIST_LINES_CTE.format(
        where_clause=where_clause,
        _on_time_case=on_time_case,
        _line_unit=_LINE_UNIT_SQL,
    )


def build_sales_order_otd_sql(
    *,
    where_clause: str,
    reference_end_date: Optional[str],
) -> Tuple[str, tuple]:
    reference_date = _reference_date_param(reference_end_date)

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
            LEFT JOIN SA1010 SA1 WITH (NOLOCK)
                ON  SA1.A1_COD = C5.C5_CLIENTE
                AND SA1.A1_LOJA = C5.C5_LOJACLI
                AND SA1.D_E_L_E_T_ = ''
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


def build_sales_order_otd_analysis_summary_sql(
    *,
    where_clause: str,
    reference_end_date: Optional[str],
) -> Tuple[str, tuple]:
    """Summary with qty + fulfillment + OTD for consolidated analysis route."""
    reference_date = _reference_date_param(reference_end_date)
    on_time = _SALES_ORDER_OTD_ON_TIME_CASE.replace("C6_DATFAT", "C6.C6_DATFAT").replace(
        "C6_ENTREG", "C6.C6_ENTREG"
    )
    sql = f"""
        WITH linhas_elegiveis AS (
            SELECT DISTINCT
                C6.C6_FILIAL,
                C6.C6_NUM,
                C6.C6_ITEM,
                C6.C6_ENTREG,
                C6.C6_DATFAT,
                CONVERT(FLOAT, ISNULL(C6.C6_QTDVEN, 0)) AS qty_sold,
                CONVERT(FLOAT, ISNULL(C6.C6_QTDENT, 0)) AS qty_delivered,
                {_LINE_UNIT_SQL} AS unit,
                {on_time} AS is_on_time
            FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
                ON  C5.C5_FILIAL = C6.C6_FILIAL
                AND C5.C5_NUM = C6.C6_NUM
            {_SB1_JOIN_SQL}
            LEFT JOIN SA1010 SA1 WITH (NOLOCK)
                ON  SA1.A1_COD = C5.C5_CLIENTE
                AND SA1.A1_LOJA = C5.C5_LOJACLI
                AND SA1.D_E_L_E_T_ = ''
            WHERE {where_clause}
        )
        SELECT
            COUNT(*) AS total_lines,
            SUM(qty_sold) AS total_qty,
            SUM(qty_delivered) AS fulfilled_qty,
            SUM(is_on_time) AS on_time_lines,
            SUM(CASE WHEN is_on_time = 0 THEN 1 ELSE 0 END) AS late_lines,
            CAST(
                CASE
                    WHEN SUM(qty_sold) = 0 THEN NULL
                    ELSE SUM(qty_delivered) * 100.0 / SUM(qty_sold)
                END
            AS DECIMAL(10, 2)) AS fulfillment_pct,
            CAST(
                CASE
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE SUM(is_on_time) * 100.0 / COUNT(*)
                END
            AS DECIMAL(10, 2)) AS otd_pct,
            {_AGG_UNIT_SELECT_SQL}
        FROM linhas_elegiveis
    """
    # on_time case embeds one '?' for reference date
    return sql, (reference_date,)


def build_sales_order_otd_analysis_by_customer_sql(
    *,
    where_clause: str,
    reference_end_date: Optional[str],
) -> Tuple[str, tuple]:
    reference_date = _reference_date_param(reference_end_date)
    on_time = _SALES_ORDER_OTD_ON_TIME_CASE.replace("C6_DATFAT", "C6.C6_DATFAT").replace(
        "C6_ENTREG", "C6.C6_ENTREG"
    )
    sql = f"""
        WITH linhas_elegiveis AS (
            SELECT DISTINCT
                C6.C6_FILIAL AS branch,
                RTRIM(LTRIM(C5.C5_CLIENTE)) AS customer_code,
                RTRIM(LTRIM(C5.C5_LOJACLI)) AS customer_store,
                COALESCE(
                    NULLIF(RTRIM(LTRIM(SA1.A1_NREDUZ)), ''),
                    RTRIM(LTRIM(SA1.A1_NOME))
                ) AS customer_name,
                C6.C6_NUM,
                C6.C6_ITEM,
                CONVERT(FLOAT, ISNULL(C6.C6_QTDVEN, 0)) AS qty_sold,
                CONVERT(FLOAT, ISNULL(C6.C6_QTDENT, 0)) AS qty_delivered,
                {_LINE_UNIT_SQL} AS unit,
                {on_time} AS is_on_time
            FROM SC6010 C6 WITH (NOLOCK)
            INNER JOIN SC5010 C5 WITH (NOLOCK)
                ON  C5.C5_FILIAL = C6.C6_FILIAL
                AND C5.C5_NUM = C6.C6_NUM
            {_SB1_JOIN_SQL}
            LEFT JOIN SA1010 SA1 WITH (NOLOCK)
                ON  SA1.A1_COD = C5.C5_CLIENTE
                AND SA1.A1_LOJA = C5.C5_LOJACLI
                AND SA1.D_E_L_E_T_ = ''
            WHERE {where_clause}
        )
        SELECT
            customer_code,
            customer_store,
            MAX(customer_name) AS customer_name,
            MAX(branch) AS branch,
            COUNT(*) AS total_lines,
            SUM(qty_sold) AS total_qty,
            SUM(qty_delivered) AS fulfilled_qty,
            SUM(is_on_time) AS on_time_lines,
            SUM(CASE WHEN is_on_time = 0 THEN 1 ELSE 0 END) AS late_lines,
            CAST(
                CASE
                    WHEN SUM(qty_sold) = 0 THEN NULL
                    ELSE SUM(qty_delivered) * 100.0 / SUM(qty_sold)
                END
            AS DECIMAL(10, 2)) AS fulfillment_pct,
            CAST(
                CASE
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE SUM(is_on_time) * 100.0 / COUNT(*)
                END
            AS DECIMAL(10, 2)) AS otd_pct,
            {_AGG_UNIT_SELECT_SQL}
        FROM linhas_elegiveis
        GROUP BY customer_code, customer_store
        ORDER BY total_qty DESC, customer_code ASC
    """
    return sql, (reference_date,)


def _status_filter_clause(status: Optional[str]) -> str:
    normalized = (status or "").strip().lower()
    if normalized == "on_time":
        return "WHERE status = 'on_time'"
    if normalized == "late":
        return "WHERE status = 'late'"
    return ""


def _search_filter_clause(search: Optional[str]) -> Tuple[str, tuple]:
    term = (search or "").strip()
    if not term or len(term) > 80:
        return "", ()
    pattern = f"%{term}%"
    clause = """
      AND (
        order_number LIKE ?
        OR customer_code LIKE ?
        OR ISNULL(customer_name, '') LIKE ?
        OR ISNULL(customer_short_name, '') LIKE ?
        OR product_code LIKE ?
        OR ISNULL(product_description, '') LIKE ?
      )
    """
    return clause, (pattern,) * 6


def sales_order_otd_search_params(search: Optional[str]) -> tuple:
    """Bind params for panel list/count search (empty when search is blank)."""
    _, params = _search_filter_clause(search)
    return params


def _post_cte_where_clause(
    *,
    status: Optional[str],
    search: Optional[str] = None,
) -> Tuple[str, tuple]:
    status_sql = _status_filter_clause(status)
    search_sql, search_params = _search_filter_clause(search)
    if not status_sql and not search_sql:
        return "", ()
    if status_sql:
        return f"{status_sql}{search_sql}", search_params
    return f"WHERE 1=1{search_sql}", search_params


def _list_order_clause(request: GetSalesOrderOtdPanelRequest) -> str:
    sort_columns = {
        "status": "status",
        "branch": "branch",
        "order_number": "order_number",
        "line_item": "line_item",
        "product_code": "product_code",
        "product_description": "product_description",
        "unit": "unit",
        "customer_code": "customer_code",
        "customer_name": "customer_name",
        "customer_short_name": "customer_short_name",
        "promised_date": "promised_date",
        "invoice_date": "invoice_date",
        "qty_sold": "qty_sold",
        "qty_delivered": "qty_delivered",
        "days_diff": "days_diff",
    }
    sort_key = (request.sort_by or "").strip().lower()
    sort_column = sort_columns.get(sort_key)
    if sort_column:
        direction = "DESC" if str(request.sort_dir or "asc").lower() == "desc" else "ASC"
        tie_breakers = [
            column
            for column in ("branch", "order_number", "line_item")
            if column != sort_column
        ]
        tie_breaker_sql = ", ".join(f"{column} ASC" for column in tie_breakers)
        return f"""
            ORDER BY {sort_column} {direction},
                     {tie_breaker_sql}
        """

    return """
        ORDER BY status DESC,
                 promised_date DESC,
                 branch ASC,
                 order_number ASC,
                 line_item ASC
    """


def build_sales_order_otd_lines_count_sql(
    *,
    where_clause: str,
    status: Optional[str],
    reference_end_date: Optional[str],
    search: Optional[str] = None,
) -> Tuple[str, tuple]:
    reference_date = _reference_date_param(reference_end_date)
    post_where, search_params = _post_cte_where_clause(status=status, search=search)
    list_cte = _list_cte_sql(where_clause=where_clause)

    sql = f"""
        WITH {list_cte}
        SELECT COUNT(*) AS total
        FROM LINHAS_ELEGIVEIS
        {post_where}
    """

    return sql, (reference_date, reference_date, reference_date) + search_params


def build_sales_order_otd_lines_list_sql(
    *,
    where_clause: str,
    request: GetSalesOrderOtdPanelRequest,
    reference_end_date: Optional[str],
) -> Tuple[str, tuple]:
    reference_date = _reference_date_param(reference_end_date)
    post_where, search_params = _post_cte_where_clause(
        status=request.status,
        search=request.search,
    )
    order_clause = _list_order_clause(request)
    list_cte = _list_cte_sql(where_clause=where_clause)

    sql = f"""
        WITH {list_cte}
        SELECT *
        FROM LINHAS_ELEGIVEIS
        {post_where}
        {order_clause}
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """

    return sql, (reference_date, reference_date, reference_date) + search_params


def build_sales_order_otd_late_days_stats_sql(
    *,
    where_clause: str,
    reference_end_date: Optional[str],
) -> Tuple[str, tuple]:
    reference_date = _reference_date_param(reference_end_date)
    list_cte = _list_cte_sql(where_clause=where_clause)
    sql = f"""
        WITH {list_cte},
        LATE_LINES AS (
            SELECT days_diff
            FROM LINHAS_ELEGIVEIS
            WHERE status = 'late'
              AND days_diff > 0
        )
        SELECT TOP 1
            AVG(CAST(days_diff AS FLOAT)) OVER () AS avg_late_days,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_diff) OVER () AS p50_late_days,
            PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY days_diff) OVER () AS p90_late_days
        FROM LATE_LINES
    """
    return sql, (reference_date, reference_date, reference_date)


def build_sales_order_otd_recurring_customers_sql(
    *,
    where_clause: str,
    reference_end_date: Optional[str],
) -> Tuple[str, tuple]:
    reference_date = _reference_date_param(reference_end_date)
    list_cte = _list_cte_sql(where_clause=where_clause)
    sql = f"""
        WITH {list_cte}
        SELECT TOP 10
            customer_code,
            customer_store,
            MAX(customer_name) AS customer_name,
            MAX(customer_short_name) AS customer_short_name,
            COUNT(*) AS late_count,
            SUM(days_diff) AS total_late_days
        FROM LINHAS_ELEGIVEIS
        WHERE status = 'late'
        GROUP BY customer_code, customer_store
        HAVING COUNT(*) >= 2
        ORDER BY late_count DESC, total_late_days DESC, customer_code ASC, customer_store ASC
    """
    return sql, (reference_date, reference_date, reference_date)


def build_sales_order_otd_worst_delays_sql(
    *,
    where_clause: str,
    reference_end_date: Optional[str],
) -> Tuple[str, tuple]:
    reference_date = _reference_date_param(reference_end_date)
    list_cte = _list_cte_sql(where_clause=where_clause)
    sql = f"""
        WITH {list_cte}
        SELECT TOP 10 *
        FROM LINHAS_ELEGIVEIS
        WHERE status = 'late'
        ORDER BY days_diff DESC, promised_date ASC, branch ASC, order_number ASC, line_item ASC
    """
    return sql, (reference_date, reference_date, reference_date)


def build_sales_order_otd_upcoming_promises_sql(
    *,
    where_clause: str,
    reference_end_date: Optional[str],
) -> Tuple[str, tuple]:
    reference_date = _reference_date_param(reference_end_date)
    list_cte = _list_cte_sql(where_clause=where_clause)
    sql = f"""
        WITH {list_cte}
        SELECT TOP 10 *
        FROM LINHAS_ELEGIVEIS
        WHERE is_invoiced = 0
        ORDER BY promised_date ASC, branch ASC, order_number ASC, line_item ASC
    """
    return sql, (reference_date, reference_date, reference_date)


def build_sales_order_otd_line_detail_sql(
    *,
    where_clause: str,
) -> str:
    list_cte = _list_cte_sql(where_clause=where_clause)

    return f"""
        WITH {list_cte}
        SELECT TOP 1 *
        FROM LINHAS_ELEGIVEIS
    """


def build_sales_order_otd_line_detail_where(
    *,
    branch: str,
    order_number: str,
    line_item: str,
    start_date: Optional[str],
    end_date: Optional[str],
    customer_segment: Optional[str],
    customer_codes: Optional[list[str]] = None,
    customer_code_stores: Optional[list[tuple[str, str]]] = None,
) -> Tuple[str, tuple]:
    where_clause, where_params = build_sales_order_otd_filters(
        branch=branch,
        start_date=start_date,
        end_date=end_date,
        customer_segment=customer_segment,
        customer_codes=customer_codes,
        customer_code_stores=customer_code_stores,
    )
    where_clause = (
        f"{where_clause} "
        "AND LTRIM(RTRIM(C6.C6_NUM)) = LTRIM(RTRIM(?)) "
        "AND LTRIM(RTRIM(C6.C6_ITEM)) = LTRIM(RTRIM(?))"
    )
    return where_clause, where_params + (order_number, line_item)


def compose_sales_order_otd_lines_params(
    *,
    where_params: tuple,
    reference_end_date: Optional[str],
    search_params: tuple = (),
    offset: Optional[int] = None,
    page_size: Optional[int] = None,
) -> tuple:
    """Placeholders de referência aparecem no SELECT antes do WHERE na CTE."""
    reference_date = _reference_date_param(reference_end_date)
    reference_params = (reference_date, reference_date, reference_date)
    params = reference_params + where_params + tuple(search_params or ())
    if offset is not None and page_size is not None:
        return params + (offset, page_size)
    return params
