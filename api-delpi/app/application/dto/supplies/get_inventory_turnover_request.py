from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch

@dataclass
class GetInventoryTurnoverRequest:
    branch: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    strict_idd_period: bool = False


    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
