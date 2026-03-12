# app/infrastructure/persistence/totvs/product_repositories/product_sales_open_orders_repository.py
from app.infrastructure.persistence.base_repository import BaseRepository

from app.domain.entities.product_sales_open_orders import ProductSalesOpenOrders
from app.domain.ports.product_sales_open_orders_repository_port import ProductSalesOpenOrdersRepositoryPort


class ProductSalesOpenOrdersRepository(
    BaseRepository,
    ProductSalesOpenOrdersRepositoryPort
):

    def get_sales_open_orders(
        self,
        code: str
    ) -> ProductSalesOpenOrders:

        sql = """
        SELECT
            SUM(C6_QTDVEN - C6_QTDENT)                 AS open_quantity,
            SUM((C6_QTDVEN - C6_QTDENT) * C6_PRCVEN)   AS open_value,
            COUNT(DISTINCT C6_NUM)                     AS orders
        FROM SC6010
        WHERE D_E_L_E_T_ = ''
        AND C6_PRODUTO = ?
        AND (C6_QTDVEN - C6_QTDENT) > 0
        AND (C6_BLOQUEI IS NULL OR C6_BLOQUEI = '')
        AND (C6_BLQ IS NULL OR C6_BLQ = '')
        """

        with self as repo:

            row = repo.execute_one(sql, (code,))

        return ProductSalesOpenOrders(
            quantity=float(row["open_quantity"] or 0),
            value=float(row["open_value"] or 0),
            orders=int(row["orders"] or 0)
        )