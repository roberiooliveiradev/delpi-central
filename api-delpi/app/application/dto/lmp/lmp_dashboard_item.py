# app/application/dto/lmp/lmp_dashboard_item.py
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class LMPDashboardItem:
    sale_number: str
    sale_description: str
    start_date: Optional[str]
    end_date: Optional[str]
    engineering_status: Optional[str]
    qtd_pi: int

    nivel: str
    dias_uteis_sla: int
    sla_minutos: int
    engineering_total_minutes: int
    data_limite: Optional[str]
    lead_time_util: Optional[int]
    status: str

    def to_dict(self) -> dict:
        return asdict(self)