from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass
class ProductRawMaterialPriceRequest:
    code: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None
    history_limit: Optional[int] = None

    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
