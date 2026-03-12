# app/domain/ports/product_purchases_repository_port.py
from abc import ABC, abstractmethod

from app.application.models.page import Page
from app.domain.entities.purchase import Purchase


class ProductPurchasesRepositoryPort(ABC):

    @abstractmethod
    def list_purchases(
        self,
        code: str,
        page: int,
        page_size: int
    ) -> Page[Purchase]:
        pass