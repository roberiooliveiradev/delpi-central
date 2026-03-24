# app/domain/entities/ppm/ppm_summary.py

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class PpmSummary:
    type: str
    branch: Optional[str]
    date_start: Optional[str]
    date_end: Optional[str]
    total_devolvido_un: float
    total_produzido_milheiro: float
    total_produzido_un: float
    ppm: float

    def to_dict(self)->dict:
        return asdict(self)