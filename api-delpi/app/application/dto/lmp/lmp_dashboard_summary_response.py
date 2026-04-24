from dataclasses import dataclass


@dataclass(frozen=True)
class LMPDashboardSummaryResponse:
    total_lmps: int
    percent_dentro_prazo: float
    avg_lead_time: float

    def to_dict(self) -> dict:
        return {
            "total_lmps": self.total_lmps,
            "percent_dentro_prazo": self.percent_dentro_prazo,
            "avg_lead_time": self.avg_lead_time,
        }