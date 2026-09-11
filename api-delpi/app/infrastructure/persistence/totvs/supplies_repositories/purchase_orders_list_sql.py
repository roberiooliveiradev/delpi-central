"""SQL builders — open purchase order lines (SC7) worklist."""

from __future__ import annotations

from datetime import date

from app.domain.services.pagination_tier_service import PaginationTierService
from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_sql import (
    branch_filter_and,
)

MAX_PAGE_SIZE = int(PaginationTierService.max_size("page_50_200") or 0)
DEFAULT_PAGE_SIZE = PaginationTierService.require_int("page_50_200", None)


def _protheus_date_param(iso_date: str) -> str:
    return iso_date.replace("-", "")


def _today_protheus(*, reference: date | None = None) -> str:
    return (reference or date.today()).strftime("%Y%m%d")


def build_purchase_orders_list_filters(
    *,
    branch: str,
    order_number: str | None = None,
    product_code: str | None = None,
    supplier_code: str | None = None,
    expected_delivery_from: str | None = None,
    expected_delivery_to: str | None = None,
    late_only: bool = False,
    reference: date | None = None,
) -> tuple[str, list]:
    """Open SC7 lines: D_E_L_E_T_='', residual <> 'S', C7_QUANT > C7_QUJE."""
    branch_clause, branch_params = branch_filter_and("RTRIM(SC7.C7_FILIAL)", branch)
    filters = [
        "SC7.D_E_L_E_T_ = ''",
        "ISNULL(SC7.C7_RESIDUO, '') <> 'S'",
        "SC7.C7_QUANT > SC7.C7_QUJE",
    ]
    params: list = list(branch_params)
    if branch_clause:
        filters.append(branch_clause.strip().removeprefix("AND ").strip())
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


def build_purchase_orders_list_sql(*, where_clause: str) -> str:
    """Paged open PO lines with open_value formula aligned to open_purchase_orders_sql."""
    return f"""
    SELECT
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
        RTRIM(COALESCE(SA2.A2_NREDUZ, SA2.A2_NOME, '')) AS supplier_name,
        CAST(ISNULL(SC7.C7_PRECO, 0) AS FLOAT) AS unit_price,
        CAST(
            ROUND(ISNULL(SC7.C7_TOTAL, 0) * bf.balance_factor, 2)
            + ROUND(ISNULL(SC7.C7_VALIPI, 0) * bf.balance_factor, 2)
            + ROUND(ISNULL(SC7.C7_VALFRE, 0) * bf.balance_factor, 2)
            - ROUND(ISNULL(SC7.C7_VLDESC, 0) * bf.balance_factor, 2)
            AS FLOAT
        ) AS open_value
    FROM SC7010 SC7 WITH (NOLOCK)
    CROSS APPLY (
        SELECT
            CASE
                WHEN ISNULL(SC7.C7_QUANT, 0) <= 0 THEN CAST(0 AS FLOAT)
                WHEN SC7.C7_QUANT > SC7.C7_QUJE
                THEN (SC7.C7_QUANT - SC7.C7_QUJE) * 1.0 / SC7.C7_QUANT
                ELSE CAST(0 AS FLOAT)
            END AS balance_factor
    ) bf
    LEFT JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = SC7.C7_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
    LEFT JOIN SA2010 SA2 WITH (NOLOCK)
        ON SA2.A2_COD = SC7.C7_FORNECE
       AND SA2.A2_LOJA = SC7.C7_LOJA
       AND SA2.D_E_L_E_T_ = ''
    WHERE {where_clause}
    ORDER BY
        CASE WHEN RTRIM(SC7.C7_DATPRF) = '' THEN 1 ELSE 0 END,
        SC7.C7_DATPRF ASC,
        SC7.C7_NUM ASC,
        SC7.C7_ITEM ASC
    OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
