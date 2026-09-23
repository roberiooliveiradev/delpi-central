from dataclasses import dataclass
from typing import Sequence

from app.domain.production.operation_materials_scope import normalize_production_orders
from app.domain.totvs.protheus_branches import normalize_branch_code


@dataclass(frozen=True)
class ListProductionOrderOperationMaterialsBatchRequest:
    production_orders: Sequence[str]
    branch: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch", normalize_branch_code(self.branch))
        object.__setattr__(
            self,
            "production_orders",
            normalize_production_orders(self.production_orders),
        )
