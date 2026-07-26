# app/application/dto/kaizen/kaizen_summary_response.py
from dataclasses import dataclass, field
from typing import List, Optional
from app.domain.entities.kaizen.kaizen import Kaizen


@dataclass
class KaizenSummaryResponse:
    start_date: Optional[str]
    end_date: Optional[str]
    total_kaizens: int
    total_savings: float
    list_kaizen: List[Kaizen] = field(default_factory=list)
    # Implantados que contribuem para total_savings (pode diferir de list_kaizen).
    list_savings_kaizen: List[Kaizen] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_kaizens": self.total_kaizens,
            "total_savings": self.total_savings,
            "list_kaizen": [item.to_dict() for item in self.list_kaizen],
            "list_savings_kaizen": [item.to_dict() for item in self.list_savings_kaizen],
        }