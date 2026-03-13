# app/domain/ports/product_guide_repository_port.py

from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.product.guide_operation import GuideOperation


class ProductGuideRepositoryPort(ABC):

    @abstractmethod
    def fetch_guide_rows(
        self,
        code: str,
        branch: Optional[str],
        max_depth: int
    ) -> List[GuideOperation]:
        pass