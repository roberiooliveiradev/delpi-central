from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass
class ProductDirectivesRequest:
    identifier: str
    max_depth: Optional[int] = None
    branch: Optional[str] = None

    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
