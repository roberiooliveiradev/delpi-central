from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass
class ProductionRequest:
    branch: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]

    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
