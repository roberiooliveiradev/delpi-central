# app/domain/ports/product_sales_open_orders_repository_port.py
from abc import ABC, abstractmethod

from app.domain.entities.product_sales_open_orders import ProductSalesOpenOrders


class ProductSalesOpenOrdersRepositoryPort(ABC):

    @abstractmethod
    def get_sales_open_orders(
        self,
        code: str
    ) -> ProductSalesOpenOrders:
        pass