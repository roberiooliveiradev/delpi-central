from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class OverallEquipmentEffectiveness:
    branch: Optional[str] = None
    oee_pct: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    def to_dict(self):
        return asdict(self)