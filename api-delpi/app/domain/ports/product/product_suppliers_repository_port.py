# app/domain/ports/product_suppliers_repository_port.py
from abc import ABC, abstractmethod
from app.application.models.page import Page
from app.domain.entities.product.supplier import Supplier


class ProductSuppliersRepositoryPort(ABC):

    @abstractmethod
    def list_suppliers(
        self,
        code: str,
        page: int,
        page_size: int
    ) -> Page[Supplier]:
        raise NotImplementedError

    @abstractmethod
    def list_suppliers_for_codes(self, codes: list[str]) -> list[dict]:
        raise NotImplementedError