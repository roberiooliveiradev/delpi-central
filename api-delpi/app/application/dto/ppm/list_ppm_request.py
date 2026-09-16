# app/application/dto/ppm/list_ppm_request.py

from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch

@dataclass
class ListPpmRequest:
    type: str                   # internal | external
    branch: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    product_prefix: Optional[str] = None


    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
