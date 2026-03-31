from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class ProductionCost:
    branch: Optional[str] = None
    date: Optional[str] = None
    cost: Optional[float] = None

    def to_dict(self):
        return asdict(self)