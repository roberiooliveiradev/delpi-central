# app/domain/ports/product_sales_billing_repository_port.py
from abc import ABC, abstractmethod

from app.domain.entities.product_sales_billing import ProductSalesBilling


class ProductSalesBillingRepositoryPort(ABC):

    @abstractmethod
    def get_sales_billing(
        self,
        code: str
    ) -> ProductSalesBilling:
        pass