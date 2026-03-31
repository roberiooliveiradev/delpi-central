from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class ProductionResponse:
    direct_labor_cost_pct: Optional[float] = None
    production_cost_pct: Optional[float] = None
    depreciation_pct: Optional[float] = None
    oee: Optional[float] = None
    otd: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)