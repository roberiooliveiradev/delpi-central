from dataclasses import dataclass, field
from typing import Optional, Sequence

from app.domain.totvs.protheus_branches import optional_concrete_branch

@dataclass
class GetCPVRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    top_limit: int = 5
    cfops: Sequence[str] = field(default_factory=lambda: ("5101", "5124", "6101", "6124"))


    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
