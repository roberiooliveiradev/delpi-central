from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass
class ProductPlaybookRequest:
    code: str
    max_depth: Optional[int] = None
    reference_date: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None
    legacy: bool = False

    def __post_init__(self) -> None:
        # Wire all → None so repository ``if branch:`` never filters B*_FILIAL='all'.
        self.branch = optional_concrete_branch(self.branch)
