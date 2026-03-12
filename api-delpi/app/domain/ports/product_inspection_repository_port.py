# app/domain/ports/product_inspection_repository_port.py
from abc import ABC, abstractmethod
from typing import List
from app.domain.entities.inspection import Inspection


class ProductInspectionRepositoryPort(ABC):

    @abstractmethod
    def list_inspections(self, code: str, max_depth: int) -> List[Inspection]:
        pass