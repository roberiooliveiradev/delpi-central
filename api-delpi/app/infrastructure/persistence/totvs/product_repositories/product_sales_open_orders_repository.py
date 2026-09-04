# app/infrastructure/persistence/totvs/product_repositories/product_sales_open_orders_repository.py
from __future__ import annotations

from app.domain.entities.product.product_sales_open_orders import ProductSalesOpenOrders
from app.domain.ports.product.product_sales_open_orders_repository_port import (
    ProductSalesOpenOrdersRepositoryPort,
)
from app.domain.totvs.protheus_branches import optional_concrete_branch
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

_OPEN_LINE_FILTERS = """
        C6.D_E_L_E_T_ = ''
        AND C5.D_E_L_E_T_ = ''
        AND C6.C6_PRODUTO = ?
        AND (C6.C6_QTDVEN - C6.C6_QTDENT) > 0
        AND (C6.C6_BLOQUEI IS NULL OR RTRIM(C6.C6_BLOQUEI) = '')
        AND (C6.C6_BLQ IS NULL OR RTRIM(C6.C6_BLQ) = '')
"""

_CUSTOMER_NAME = """
        COALESCE(
            NULLIF(RTRIM(LTRIM(SA1.A1_NREDUZ)), ''),
            RTRIM(LTRIM(SA1.A1_NOME)),
            ''
        )
"""


class ProductSalesOpenOrdersRepository(
    BaseRepository,
    ProductSalesOpenOrdersRepositoryPort,
):

    def get_sales_open_orders(
        self,
        code: str,
        *,
        branch: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> ProductSalesOpenOrders:
        concrete_branch = optional_concrete_branch(branch)
        page = max(1, int(page or 1))
        page_size = min(max(1, int(page_size or 50)), 200)
        offset = (page - 1) * page_size

        where = _OPEN_LINE_FILTERS
        params: list = [code]
        if concrete_branch:
            where += " AND C6.C6_FILIAL = ?"
            params.append(concrete_branch)

        summary_sql = f"""
        SELECT
            SUM(C6.C6_QTDVEN - C6.C6_QTDENT) AS open_quantity,
            SUM((C6.C6_QTDVEN - C6.C6_QTDENT) * C6.C6_PRCVEN) AS open_value,
            COUNT(DISTINCT C6.C6_NUM) AS orders,
            COUNT(*) AS line_count
        FROM SC6010 C6 WITH (NOLOCK)
        INNER JOIN SC5010 C5 WITH (NOLOCK)
            ON C5.C5_FILIAL = C6.C6_FILIAL
            AND C5.C5_NUM = C6.C6_NUM
        WHERE {where}
        """

        items_sql = f"""
        SELECT
            RTRIM(LTRIM(C6.C6_FILIAL)) AS branch,
            RTRIM(LTRIM(C6.C6_NUM)) AS order_number,
            RTRIM(LTRIM(C6.C6_ITEM)) AS order_item,
            RTRIM(LTRIM(C5.C5_CLIENTE)) AS customer_code,
            RTRIM(LTRIM(C5.C5_LOJACLI)) AS customer_store,
            {_CUSTOMER_NAME} AS customer_name,
            (C6.C6_QTDVEN - C6.C6_QTDENT) AS open_quantity,
            C6.C6_PRCVEN AS unit_price,
            (C6.C6_QTDVEN - C6.C6_QTDENT) * C6.C6_PRCVEN AS open_value,
            CONVERT(VARCHAR(10), C6.C6_ENTREG, 23) AS delivery_date,
            CONVERT(VARCHAR(10), C5.C5_EMISSAO, 23) AS issue_date
        FROM SC6010 C6 WITH (NOLOCK)
        INNER JOIN SC5010 C5 WITH (NOLOCK)
            ON C5.C5_FILIAL = C6.C6_FILIAL
            AND C5.C5_NUM = C6.C6_NUM
        LEFT JOIN SA1010 SA1 WITH (NOLOCK)
            ON SA1.A1_COD = C5.C5_CLIENTE
            AND SA1.A1_LOJA = C5.C5_LOJACLI
            AND SA1.D_E_L_E_T_ = ''
        WHERE {where}
        ORDER BY
            CASE
                WHEN C6.C6_ENTREG IS NULL OR RTRIM(CAST(C6.C6_ENTREG AS VARCHAR(20))) = ''
                THEN 1 ELSE 0
            END,
            C6.C6_ENTREG,
            C6.C6_NUM,
            C6.C6_ITEM
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:
            summary_row = repo.execute_one(summary_sql, tuple(params)) or {}
            items = repo.execute_query(
                items_sql,
                tuple([*params, offset, page_size]),
            ) or []

        total_lines = int(summary_row.get("line_count") or 0)
        total_pages = (total_lines + page_size - 1) // page_size if total_lines else 0

        return ProductSalesOpenOrders(
            items=[dict(row) for row in items],
            quantity=float(summary_row.get("open_quantity") or 0),
            value=float(summary_row.get("open_value") or 0),
            orders=int(summary_row.get("orders") or 0),
            page=page,
            page_size=page_size,
            total=total_lines,
            total_pages=total_pages,
        )
