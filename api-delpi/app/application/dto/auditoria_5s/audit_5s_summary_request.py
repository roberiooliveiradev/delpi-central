from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch

@dataclass
class Audit5SSummaryRequest:
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    branch: Optional[str] = None


    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
