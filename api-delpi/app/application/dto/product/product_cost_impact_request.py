from dataclasses import dataclass
from typing import Literal, Optional

PriceSource = Literal["standard_cost", "last_purchase"]


@dataclass
class ProductCostImpactRequest:
    code: str
    max_depth: Optional[int] = None
    price_source: PriceSource = "standard_cost"
    adjustment_percent: float = 0.0
    top_n: Optional[int] = None
