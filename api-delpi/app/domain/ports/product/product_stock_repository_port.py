# app/domain/ports/product_stock_repository_port.py

from abc import ABC, abstractmethod
from typing import Optional
from app.application.models.page import Page
from app.domain.entities.product.stock import Stock


class ProductStockRepositoryPort(ABC):

    @abstractmethod
    def list_stock(
        self,
        code: str,
        page: int,
        page_size: int,
        branch: Optional[str],
        location: Optional[str]
    ) -> Page[Stock]:
        pass