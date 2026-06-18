from __future__ import annotations

from dataclasses import dataclass


@dataclass
class InspecoesEntradaResumoResponse:
    branch: str
    pending_inspections: int = 0
    inspected: int = 0
    approved_inspections: int = 0
    rejected_inspections: int = 0
    approval_rate: float = 0.0
    inspections_with_time: int = 0
    average_time_hours: float = 0.0
    average_time_days: float = 0.0

    def to_dict(self) -> dict:
        return {
            "branch": self.branch,
            "pending_inspections": self.pending_inspections,
            "inspected": self.inspected,
            "approved_inspections": self.approved_inspections,
            "rejected_inspections": self.rejected_inspections,
            "approval_rate": self.approval_rate,
            "inspections_with_time": self.inspections_with_time,
            "average_time_hours": self.average_time_hours,
            "average_time_days": self.average_time_days,
        }
