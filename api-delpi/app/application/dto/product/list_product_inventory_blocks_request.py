from dataclasses import dataclass
from typing import Sequence

from app.domain.totvs.protheus_branches import normalize_branch_code
from app.domain.totvs.protheus_product_codes import require_product_codes
from app.domain.totvs.protheus_warehouses import WAREHOUSE_ALMOXARIFADO


@dataclass(frozen=True)
class ListProductInventoryBlocksRequest:
    product_codes: Sequence[str]
    branch: str
    warehouse: str = WAREHOUSE_ALMOXARIFADO

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch", normalize_branch_code(self.branch))
        warehouse = str(self.warehouse or "").strip() or WAREHOUSE_ALMOXARIFADO
        object.__setattr__(self, "warehouse", warehouse)
        object.__setattr__(
            self,
            "product_codes",
            require_product_codes(self.product_codes),
        )
