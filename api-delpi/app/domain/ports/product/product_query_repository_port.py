# app/domain/ports/product_repository_port.py
from abc import ABC, abstractmethod
from typing import Optional
from app.application.models.page import Page
from app.domain.entities.product.product import Product

class ProductQueryRepositoryPort(ABC):
    @abstractmethod
    def fetch_product_by_code(self, code: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def fetch_product_by_customer_reference(self, reference: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def search_products(
        self,
        code: Optional[str],
        group: Optional[str],
        description: Optional[str],
        customer_reference: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        sort=Optional[str],
        direction=Optional[str]
    ) -> Page[Product]:
        raise NotImplementedError