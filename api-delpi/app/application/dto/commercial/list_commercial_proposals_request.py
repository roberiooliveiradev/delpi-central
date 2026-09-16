from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch

@dataclass
class ListCommercialProposalsRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 50
    customer_segment: Optional[str] = None
    customer_codes: Optional[list[str]] = None
    sort_by: Optional[str] = None
    sort_dir: str = "asc"
    search: Optional[str] = None
    product_code: Optional[str] = None
    product_group: Optional[str] = None


    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
