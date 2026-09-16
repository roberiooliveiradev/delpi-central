from dataclasses import dataclass
from typing import Literal

from app.domain.totvs.protheus_branches import optional_concrete_branch

ProductionOrderProductType = Literal["PA", "PI"]


@dataclass(frozen=True)
class GetProductionOrderByOpRequest:
    production_order: str
    branch: str | None = None
    product_type: ProductionOrderProductType | None = None
    linked_sort_by: str | None = None
    linked_sort_dir: str = "asc"

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch", optional_concrete_branch(self.branch))
