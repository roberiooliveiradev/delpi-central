# app/application/dto/auditoria_5s/audit_5s_summary_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class Audit5SSummaryRequest:
    start_date: Optional[str] = None
    end_date: Optional[str] = None