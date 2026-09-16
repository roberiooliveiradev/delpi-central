# app/application/dto/list_product_guide_request.py
from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass
class ListProductGuideRequest:

    code: str
    branch: Optional[str] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    max_depth: Optional[int] = None

    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
