# app/application/dto/lmp/lmp_dashboard_item.py
from dataclasses import dataclass, asdict
from typing import Optional

from app.application.services.lmp_business_rules import LMPBusinessRules


@dataclass
class LMPDashboardItem:
    branch: Optional[str]
    sale_number: str
    sale_description: str
    listing_kind: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    nivel: str
    dias_uteis_sla: int
    sla_minutos: int
    engineering_total_minutes: int
    data_limite: Optional[str]
    lead_time_util: Optional[int]
    status: str
    homolog_revision: Optional[str] = None
    measurement_revision: Optional[str] = None
    homolog_date: Optional[str] = None
    cycle_index: int = 1
    engineering_status: Optional[str] = None
    qtd_pi: int = 0

    def to_dict(self) -> dict:
        data = asdict(self)
        return LMPBusinessRules.format_payload_dates(
            data,
            ("start_date", "end_date", "data_limite", "homolog_date"),
        )
