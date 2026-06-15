from dataclasses import dataclass
from typing import Literal


ProductionOrderProductType = Literal["PA", "PI"]


@dataclass(frozen=True)
class GetProductionOrderByOpRequest:
    production_order: str
    branch: str | None = None
    product_type: ProductionOrderProductType | None = None
    linked_sort_by: str | None = None
    linked_sort_dir: str = "asc"
