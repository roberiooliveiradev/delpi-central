# app/domain/ports/product_repository_port.py
from abc import ABC, abstractmethod
from typing import Optional
from app.application.models.page import Page
from app.domain.entities.product import Product

class ProductQueryRepositoryPort(ABC):
    @abstractmethod
    def search_products(
        self,
        code: Optional[str],
        group: Optional[str],
        description: Optional[str],
        page: int,
        page_size: int,
    ) -> Page[Product]:
        raise NotImplementedError