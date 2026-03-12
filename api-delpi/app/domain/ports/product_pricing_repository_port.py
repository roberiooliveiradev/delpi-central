# app/domain/ports/product_pricing_repository_port.py
from abc import ABC, abstractmethod

from app.domain.entities.product_pricing import ProductPricing


class ProductPricingRepositoryPort(ABC):

    @abstractmethod
    def get_product_pricing(
        self,
        code: str
    ) -> ProductPricing | None:
        pass