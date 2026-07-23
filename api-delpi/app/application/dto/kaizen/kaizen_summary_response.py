# app/application/dto/kaizen/kaizen_summary_response.py
from dataclasses import dataclass, field
from typing import List, Optional
from app.domain.entities.kaizen.kaizen import Kaizen


@dataclass
class KaizenSummaryResponse:
    date_start: Optional[str]
    date_end: Optional[str]
    total_kaizens: int
    total_savings: float
    list_kaizen: List[Kaizen] = field(default_factory=list)
    # Implantados que contribuem para total_savings (pode diferir de list_kaizen).
    list_savings_kaizen: List[Kaizen] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date_start": self.date_start,
            "date_end": self.date_end,
            "total_kaizens": self.total_kaizens,
            "total_savings": self.total_savings,
            "list_kaizen": [item.to_dict() for item in self.list_kaizen],
            "list_savings_kaizen": [item.to_dict() for item in self.list_savings_kaizen],
        }