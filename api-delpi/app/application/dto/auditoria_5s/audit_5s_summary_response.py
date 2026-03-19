# app/application/dto/auditoria_5s/audit_5s_summary_response.py
from dataclasses import dataclass, field
from typing import List, Optional

from app.domain.entities.audit_5s.audit_5s import Audit5S


@dataclass
class Audit5SSummaryResponse:
    start_date: Optional[str]
    end_date: Optional[str]
    average_score: float
    list_audits: List[Audit5S] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "average_score": self.average_score,
            "list_audits": [item.to_dict() for item in self.list_audits],
        }