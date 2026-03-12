# app/domain/ports/product_guide_repository_port.py

from abc import ABC, abstractmethod
from app.application.models.page import Page
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
    ) -> Page[GuideOperation]:
        pass