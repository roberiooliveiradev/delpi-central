# app/domain/ports/sale/sale_order_query_repository_port.py
from abc import ABC, abstractmethod
from app.application.models.page import Page

from app.domain.entities.sale.sale_order import SaleOrder
from app.application.dto.sale_order.list_sale_order_request import ListSaleOrderRequest


class SaleOrderQueryRepositoryPort(ABC):

    @abstractmethod
    def list_sales_orders(
        self,
        request: ListSaleOrderRequest
    ) -> Page[SaleOrder]:
        raise NotImplementedError