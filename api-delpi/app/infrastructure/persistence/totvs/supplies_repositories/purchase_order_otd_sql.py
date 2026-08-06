"""SQL — OTD de pedidos de compra (MP) via VW_PONTUALIDADE_FORNECEDORES.

No prazo: DIAS >= 0. Período: DT_DIGITACAO. Universo: TIPO_PRODUTO = MP.
"""

from __future__ import annotations

from typing import Optional, Tuple

from app.application.dto.supplies.get_purchase_order_otd_panel_request import (
    GetPurchaseOrderOtdPanelRequest,
)
from app.domain.totvs.protheus_product_types import PRODUCT_TYPE_RAW_MATERIAL
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

_VIEW = "VW_PONTUALIDADE_FORNECEDORES"

_LIST_LINES_CTE = """
    LINHAS_ELEGIVEIS AS (
        SELECT
            FILIAL AS branch,
            RTRIM(LTRIM(FORNECEDOR)) AS supplier_code,
            RTRIM(LTRIM(LOJA)) AS supplier_store,
            RTRIM(LTRIM(NOME_FORNECEDOR)) AS supplier_name,
            RTRIM(LTRIM(DOCUMENTO)) AS document,
            RTRIM(LTRIM(NUMERO_PEDIDO)) AS order_number,
            RTRIM(LTRIM(ITEM_PEDIDO)) AS order_item,
            RTRIM(LTRIM(PRODUTO)) AS product_code,
            RTRIM(LTRIM(DESCRICAO_PRODUTO)) AS product_description,
            RTRIM(LTRIM(TIPO_PRODUTO)) AS product_type,
            QUANTIDADE AS quantity,
            CONVERT(VARCHAR(10), DT_EMISSAO_PC, 23) AS purchase_order_issue_date,
            CONVERT(VARCHAR(10), DT_ENTREGA, 23) AS expected_delivery_date,
            CONVERT(VARCHAR(10), DT_DIGITACAO, 23) AS receipt_entry_date,
            CONVERT(VARCHAR(10), DT_EMISSAO_NF, 23) AS invoice_issue_date,
            DIAS AS days_diff,
            CASE WHEN DIAS >= 0 THEN 1 ELSE 0 END AS is_on_time,
            CASE WHEN DIAS >= 0 THEN 'on_time' ELSE 'late' END AS status
        FROM {view} WITH (NOLOCK)
        WHERE {where_clause}
    )
"""


def build_purchase_order_otd_filters(
    *,
    branch: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
) -> Tuple[str, tuple]:
    qb = QueryBuilder()
    qb.eq("RTRIM(TIPO_PRODUTO)", PRODUCT_TYPE_RAW_MATERIAL)

    if branch:
        qb.eq("FILIAL", branch)

    qb.date_range("DT_DIGITACAO", start_date, end_date)

    return qb.build()


def build_purchase_order_otd_sql(*, where_clause: str) -> str:
    return f"""
        SELECT
            COUNT(*) AS total_lines,
            SUM(CASE WHEN DIAS >= 0 THEN 1 ELSE 0 END) AS on_time_lines,
            SUM(CASE WHEN DIAS < 0 THEN 1 ELSE 0 END) AS late_lines,
            CAST(
                CASE
                    WHEN COUNT(*) = 0 THEN NULL
                    ELSE SUM(CASE WHEN DIAS >= 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                END
            AS DECIMAL(10, 2)) AS purchase_order_otd_pct
        FROM {_VIEW} WITH (NOLOCK)
        WHERE {where_clause}
    """


def _status_filter_clause(status: Optional[str]) -> str:
    normalized = (status or "").strip().lower()
    if normalized == "on_time":
        return "WHERE status = 'on_time'"
    if normalized == "late":
        return "WHERE status = 'late'"
    return ""


def _list_order_clause(request: GetPurchaseOrderOtdPanelRequest) -> str:
    sort_columns = {
        "status": "status",
        "branch": "branch",
        "order_number": "order_number",
        "order_item": "order_item",
        "product_code": "product_code",
        "product_description": "product_description",
        "supplier_code": "supplier_code",
        "supplier_name": "supplier_name",
        "expected_delivery_date": "expected_delivery_date",
        "receipt_entry_date": "receipt_entry_date",
        "quantity": "quantity",
        "days_diff": "days_diff",
    }
    sort_key = (request.sort_by or "").strip().lower()
    sort_column = sort_columns.get(sort_key)
    if sort_column:
        direction = "DESC" if str(request.sort_dir or "asc").lower() == "desc" else "ASC"
        tie_breakers = [
            column
            for column in ("branch", "order_number", "order_item")
            if column != sort_column
        ]
        tie_breaker_sql = ", ".join(f"{column} ASC" for column in tie_breakers)
        return f"""
            ORDER BY {sort_column} {direction},
                     {tie_breaker_sql}
        """

    return """
        ORDER BY status DESC,
                 expected_delivery_date DESC,
                 branch ASC,
                 order_number ASC,
                 order_item ASC
    """


def _list_cte_sql(*, where_clause: str) -> str:
    return _LIST_LINES_CTE.format(view=_VIEW, where_clause=where_clause)


def build_purchase_order_otd_lines_count_sql(
    *,
    where_clause: str,
    status: Optional[str],
) -> str:
    status_clause = _status_filter_clause(status)
    list_cte = _list_cte_sql(where_clause=where_clause)
    return f"""
        WITH {list_cte}
        SELECT COUNT(*) AS total
        FROM LINHAS_ELEGIVEIS
        {status_clause}
    """


def build_purchase_order_otd_lines_list_sql(
    *,
    where_clause: str,
    request: GetPurchaseOrderOtdPanelRequest,
) -> str:
    status_clause = _status_filter_clause(request.status)
    order_clause = _list_order_clause(request)
    list_cte = _list_cte_sql(where_clause=where_clause)
    return f"""
        WITH {list_cte}
        SELECT *
        FROM LINHAS_ELEGIVEIS
        {status_clause}
        {order_clause}
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
