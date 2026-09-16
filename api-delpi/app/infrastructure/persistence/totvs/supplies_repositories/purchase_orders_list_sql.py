"""SQL builders — open purchase order lines (SC7) worklist."""

from __future__ import annotations

from datetime import date

from app.domain.services.pagination_tier_service import PaginationTierService
from app.domain.totvs.protheus_branches import normalize_branch_code

MAX_PAGE_SIZE = int(PaginationTierService.max_size("page_50_200") or 0)
DEFAULT_PAGE_SIZE = PaginationTierService.require_int("page_50_200", None)

PURCHASE_ORDERS_SORT_FIELDS: tuple[str, ...] = (
    "order_number",
    "order_item",
    "product_code",
    "product_description",
    "supplier_name",
    "open_quantity",
    "expected_delivery_date",
    "delivery_status",
    "open_value",
)

_DEFAULT_ORDER_BY = """
        CASE WHEN RTRIM(SC7.C7_DATPRF) = '' THEN 1 ELSE 0 END,
        SC7.C7_DATPRF ASC,
        SC7.C7_NUM ASC,
        SC7.C7_ITEM ASC
"""

# Canonical open_value = proportional C7_TOTAL + IPI + frete − desconto via balance_factor.
_OPEN_VALUE_EXPRESSION = """(
            ROUND(ISNULL(SC7.C7_TOTAL, 0) * bf.balance_factor, 2)
            + ROUND(ISNULL(SC7.C7_VALIPI, 0) * bf.balance_factor, 2)
            + ROUND(ISNULL(SC7.C7_VALFRE, 0) * bf.balance_factor, 2)
            - ROUND(ISNULL(SC7.C7_VLDESC, 0) * bf.balance_factor, 2)
        )"""

_BALANCE_FACTOR_CROSS_APPLY = """
    CROSS APPLY (
        SELECT
            CASE
                WHEN ISNULL(SC7.C7_QUANT, 0) <= 0 THEN CAST(0 AS FLOAT)
                WHEN SC7.C7_QUANT > SC7.C7_QUJE
                THEN (SC7.C7_QUANT - SC7.C7_QUJE) * 1.0 / SC7.C7_QUANT
                ELSE CAST(0 AS FLOAT)
            END AS balance_factor
    ) bf
"""

_OPEN_QUANTITY_EXPRESSION = """(
            CASE
                WHEN SC7.C7_QUANT > SC7.C7_QUJE
                THEN SC7.C7_QUANT - SC7.C7_QUJE
                ELSE 0
            END
        )"""

_DELIVERY_STATUS_SORT_EXPRESSION = """(
            CASE
                WHEN RTRIM(ISNULL(SC7.C7_DATPRF, '')) = '' THEN 2
                WHEN RTRIM(SC7.C7_DATPRF) < CONVERT(char(8), GETDATE(), 112) THEN 0
                ELSE 1
            END
        )"""

_PURCHASE_ORDERS_SORT_EXPRESSIONS: dict[str, str] = {
    "order_number": "SC7.C7_NUM",
    "order_item": "SC7.C7_ITEM",
    "product_code": "SC7.C7_PRODUTO",
    "product_description": "RTRIM(COALESCE(SB1.B1_DESC, SC7.C7_DESCRI, ''))",
    "supplier_name": "RTRIM(COALESCE(SA2.A2_NREDUZ, SA2.A2_NOME, ''))",
    "open_quantity": _OPEN_QUANTITY_EXPRESSION,
    "expected_delivery_date": "SC7.C7_DATPRF",
    "delivery_status": _DELIVERY_STATUS_SORT_EXPRESSION,
    "open_value": _OPEN_VALUE_EXPRESSION,
}


def _protheus_date_param(iso_date: str) -> str:
    return iso_date.replace("-", "")


def _today_protheus(*, reference: date | None = None) -> str:
    return (reference or date.today()).strftime("%Y%m%d")


def normalize_purchase_order_branches(
    *,
    branch: str | None = None,
    branches: list[str] | None = None,
) -> list[str]:
    """Fail-closed unit scope: at least one concrete 01|02 code, de-duplicated."""
    raw = list(branches or [])
    if not raw and branch:
        raw = [branch]
    codes: list[str] = []
    seen: set[str] = set()
    for item in raw:
        code = normalize_branch_code(str(item or "").strip())
        if code in seen:
            continue
        seen.add(code)
        codes.append(code)
    if not codes:
        raise ValueError("at least one branch is required")
    return codes


def _branch_scope_sql(codes: list[str]) -> tuple[str, list[str]]:
    if len(codes) == 1:
        return "RTRIM(SC7.C7_FILIAL) = ?", codes
    placeholders = ", ".join("?" * len(codes))
    return f"RTRIM(SC7.C7_FILIAL) IN ({placeholders})", codes


def resolve_purchase_orders_order_by(
    *,
    sort_by: str | None = None,
    sort_dir: str | None = None,
) -> str:
    """Allow-listed ORDER BY. Default remains promised date / order / item."""
    key = (sort_by or "").strip()
    if not key:
        return _DEFAULT_ORDER_BY.strip()
    expression = _PURCHASE_ORDERS_SORT_EXPRESSIONS.get(key)
    if expression is None:
        raise ValueError("Invalid sort_by")
    direction = (sort_dir or "asc").strip().lower()
    if direction not in {"asc", "desc"}:
        raise ValueError("Invalid sort_dir")
    return f"{expression} {direction.upper()}, SC7.C7_NUM ASC, SC7.C7_ITEM ASC"


def count_sql_placeholders(sql: str) -> int:
    return sql.count("?")


def split_sql_placeholder_counts(sql: str) -> tuple[int, int]:
    """Count `?` before and after the first WHERE (textual bind order)."""
    marker = "WHERE"
    upper = sql.upper()
    index = upper.find(marker)
    if index < 0:
        return count_sql_placeholders(sql), 0
    return sql[:index].count("?"), sql[index:].count("?")


def bind_purchase_orders_summary_params(
    summary_sql: str,
    where_params: list,
    *,
    today_protheus: str,
) -> tuple:
    """SELECT bucket dates bind before WHERE placeholders."""
    select_placeholders, where_placeholders = split_sql_placeholder_counts(summary_sql)
    if where_placeholders != len(where_params):
        raise ValueError(
            "summary SQL WHERE placeholders do not match filter params "
            f"({where_placeholders} != {len(where_params)})"
        )
    return (today_protheus,) * select_placeholders + tuple(where_params)


def build_purchase_orders_list_filters(
    *,
    branch: str | None = None,
    branches: list[str] | None = None,
    order_number: str | None = None,
    product_code: str | None = None,
    supplier_code: str | None = None,
    expected_delivery_from: str | None = None,
    expected_delivery_to: str | None = None,
    late_only: bool = False,
    reference: date | None = None,
) -> tuple[str, list]:
    """Open SC7 lines: D_E_L_E_T_='', residual <> 'S', C7_QUANT > C7_QUJE."""
    codes = normalize_purchase_order_branches(branch=branch, branches=branches)
    branch_clause, branch_params = _branch_scope_sql(codes)
    filters = [
        "SC7.D_E_L_E_T_ = ''",
        "ISNULL(SC7.C7_RESIDUO, '') <> 'S'",
        "SC7.C7_QUANT > SC7.C7_QUJE",
        branch_clause,
    ]
    params: list = list(branch_params)
    if order_number:
        filters.append("RTRIM(SC7.C7_NUM) = ?")
        params.append(order_number.strip())
    if product_code:
        filters.append("RTRIM(SC7.C7_PRODUTO) = ?")
        params.append(product_code.strip())
    if supplier_code:
        filters.append("RTRIM(SC7.C7_FORNECE) = ?")
        params.append(supplier_code.strip())
    if expected_delivery_from:
        filters.append("RTRIM(SC7.C7_DATPRF) >= ?")
        params.append(_protheus_date_param(expected_delivery_from))
    if expected_delivery_to:
        filters.append("RTRIM(SC7.C7_DATPRF) <= ?")
        params.append(_protheus_date_param(expected_delivery_to))
    if late_only:
        filters.append("RTRIM(ISNULL(SC7.C7_DATPRF, '')) <> ''")
        filters.append("RTRIM(SC7.C7_DATPRF) < ?")
        params.append(_today_protheus(reference=reference))
    return " AND ".join(filters), params


def build_purchase_orders_list_count_sql(where_clause: str) -> str:
    return f"""
    SELECT COUNT(1) AS total
    FROM SC7010 SC7 WITH (NOLOCK)
    WHERE {where_clause}
    """


def build_purchase_orders_summary_sql(*, where_clause: str) -> str:
    """Aggregate open PO lines for hero/chips — no pagination; caller omits late_only."""
    return f"""
    SELECT
        COUNT(1) AS total_lines,
        CAST(COALESCE(SUM{_OPEN_VALUE_EXPRESSION}, 0) AS FLOAT) AS total_open_value,
        SUM(CASE
            WHEN RTRIM(ISNULL(SC7.C7_DATPRF, '')) <> ''
             AND RTRIM(SC7.C7_DATPRF) < ?
            THEN 1 ELSE 0 END) AS late_lines,
        SUM(CASE
            WHEN RTRIM(ISNULL(SC7.C7_DATPRF, '')) <> ''
             AND RTRIM(SC7.C7_DATPRF) >= ?
            THEN 1 ELSE 0 END) AS on_time_lines,
        SUM(CASE
            WHEN RTRIM(ISNULL(SC7.C7_DATPRF, '')) = ''
            THEN 1 ELSE 0 END) AS no_date_lines
    FROM SC7010 SC7 WITH (NOLOCK)
    {_BALANCE_FACTOR_CROSS_APPLY}
    WHERE {where_clause}
    """


def _purchase_orders_select_columns(*, include_origin_and_buyer: bool) -> str:
    extra = ""
    if include_origin_and_buyer:
        extra = """
        RTRIM(ISNULL(SC7.C7_COMPRA, '')) AS buyer_code,
        NULLIF(RTRIM(ISNULL(SC7.C7_NUMSC, '')), '') AS source_request_number,
        NULLIF(RTRIM(ISNULL(SC7.C7_ITEMSC, '')), '') AS source_request_item,"""
    return f"""
        RTRIM(SC7.C7_FILIAL) AS branch,
        RTRIM(SC7.C7_NUM) AS order_number,
        RTRIM(SC7.C7_ITEM) AS order_item,
        RTRIM(SC7.C7_PRODUTO) AS product_code,
        RTRIM(COALESCE(SB1.B1_DESC, SC7.C7_DESCRI, '')) AS product_description,
        CAST(ISNULL(SC7.C7_QUANT, 0) AS FLOAT) AS ordered_quantity,
        CAST(ISNULL(SC7.C7_QUJE, 0) AS FLOAT) AS delivered_quantity,
        CAST(
            CASE
                WHEN SC7.C7_QUANT > SC7.C7_QUJE
                THEN SC7.C7_QUANT - SC7.C7_QUJE
                ELSE 0
            END AS FLOAT
        ) AS open_quantity,
        RTRIM(SC7.C7_EMISSAO) AS issue_date,
        RTRIM(SC7.C7_DATPRF) AS expected_delivery_date,
        RTRIM(SC7.C7_FORNECE) AS supplier_code,
        RTRIM(SC7.C7_LOJA) AS supplier_store,
        RTRIM(COALESCE(SA2.A2_NREDUZ, SA2.A2_NOME, '')) AS supplier_name,{extra}
        CAST(ISNULL(SC7.C7_PRECO, 0) AS FLOAT) AS unit_price,
        CAST({_OPEN_VALUE_EXPRESSION} AS FLOAT) AS open_value
    """


def _purchase_orders_from_joins() -> str:
    return f"""
    FROM SC7010 SC7 WITH (NOLOCK)
    {_BALANCE_FACTOR_CROSS_APPLY}
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SC7.C7_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = SC7.C7_FORNECE
       AND SA2.A2_LOJA = SC7.C7_LOJA
       AND SA2.D_E_L_E_T_ = ''
    """


def build_purchase_orders_list_sql(
    *,
    where_clause: str,
    order_by: str | None = None,
) -> str:
    """Paged open PO lines with open_value formula aligned to open_purchase_orders_sql."""
    resolved_order = (order_by or _DEFAULT_ORDER_BY).strip()
    return f"""
    SELECT
        {_purchase_orders_select_columns(include_origin_and_buyer=False)}
    {_purchase_orders_from_joins()}
    WHERE {where_clause}
    ORDER BY
        {resolved_order}
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """


def build_purchase_orders_export_sql(
    *,
    where_clause: str,
    order_by: str | None = None,
) -> str:
    """Unpaged open PO lines for Excel — same scope/sort as list, no OFFSET."""
    resolved_order = (order_by or _DEFAULT_ORDER_BY).strip()
    return f"""
    SELECT
        {_purchase_orders_select_columns(include_origin_and_buyer=False)}
    {_purchase_orders_from_joins()}
    WHERE {where_clause}
    ORDER BY
        {resolved_order}
    """


def build_purchase_order_detail_sql(*, where_clause: str) -> str:
    """Open PO lines for one (branch, order_number) aggregate — no pagination."""
    return f"""
    SELECT
        {_purchase_orders_select_columns(include_origin_and_buyer=True)}
    {_purchase_orders_from_joins()}
    WHERE {where_clause}
    ORDER BY SC7.C7_ITEM ASC
    """
