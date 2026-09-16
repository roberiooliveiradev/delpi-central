from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch

@dataclass
class GetOTDRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    top_limit: int = 5
    details_limit: int = 20


    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
