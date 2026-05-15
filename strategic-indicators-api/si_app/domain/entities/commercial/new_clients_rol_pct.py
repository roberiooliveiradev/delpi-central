from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class NewClientsRolPct:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_rol: float = 0
    new_clients_rol: float = 0
    new_clients_rol_pct: Optional[float] = None

    def to_dict(self):
        return asdict(self)