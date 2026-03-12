# app/domain/ports/product_internal_movements_repository_port.py

from abc import ABC, abstractmethod
from typing import Optional
from app.application.models.page import Page
from app.domain.entities.internal_movement import InternalMovement


class ProductInternalMovementsRepositoryPort(ABC):

    @abstractmethod
    def list_internal_movements(
        self,
        code: str,
        page: int,
        page_size: int,
        date_start: Optional[str],
        date_end: Optional[str],
        branch: Optional[str],
        location: Optional[str],
        tm: Optional[str],
        op: Optional[str]
    ) -> Page[InternalMovement]:
        pass