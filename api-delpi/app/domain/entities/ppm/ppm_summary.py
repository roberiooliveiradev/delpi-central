# app/domain/entities/ppm/ppm_summary.py

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class PpmSummary:
    type: str
    branch: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    total_devolvido_un: float
    total_produzido_milheiro: float
    total_produzido_un: float
    ppm: float

    def to_dict(self) -> dict:
        data = asdict(self)
        data["numerator"] = {"qty_returned_un": self.total_devolvido_un}
        data["denominator"] = {
            "qty_produced_un": self.total_produzido_un,
            "qty_produced_milheiro": self.total_produzido_milheiro,
        }
        return data
