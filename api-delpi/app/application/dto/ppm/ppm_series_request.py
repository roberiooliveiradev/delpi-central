from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch

@dataclass
class PpmSeriesRequest:
    type: str
    granularity: str
    branch: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    product_prefix: Optional[str] = None


    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
