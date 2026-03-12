# app/domain/ports/product_sales_repository_port.py
from abc import ABC, abstractmethod
from app.domain.entities.product_sales_summary import ProductSalesSummary


class ProductSalesRepositoryPort(ABC):

    @abstractmethod
    def get_sales_summary(
        self,
        code: str
    ) -> ProductSalesSummary:
        pass