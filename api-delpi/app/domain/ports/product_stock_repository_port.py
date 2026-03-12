# app/domain/ports/product_stock_repository_port.py

from abc import ABC, abstractmethod
from typing import Tuple, List, Optional
from app.domain.entities.stock import Stock


class ProductStockRepositoryPort(ABC):

    @abstractmethod
    def list_stock(
        self,
        code: str,
        page: int,
        page_size: int,
        branch: Optional[str],
        location: Optional[str]
    ) -> Tuple[int, List[Stock]]:
        pass