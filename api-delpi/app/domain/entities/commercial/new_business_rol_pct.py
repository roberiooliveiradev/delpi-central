from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class NewBusinessRolPct:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_rol: float = 0
    new_business_rol: float = 0
    weg_rol: float = 0
    new_business_rol_pct: Optional[float] = None

    def to_dict(self):
        return asdict(self)
