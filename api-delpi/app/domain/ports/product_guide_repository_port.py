# app/domain/ports/product_guide_repository_port.py
from abc import ABC, abstractmethod
from typing import Tuple, List
from app.domain.entities.guide_operation import GuideOperation


class ProductGuideRepositoryPort(ABC):

    @abstractmethod
    def list_guide(
        self,
        code: str,
        page: int,
        page_size: int,
        branch: str | None,
        max_depth: int
    ) -> Tuple[int, List[GuideOperation]]:
        pass