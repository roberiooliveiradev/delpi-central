from __future__ import annotations

from dataclasses import dataclass

@dataclass
class GetExecutiveSummaryRealRequest:
    departmant_id: str | None = None
    branch: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    competence: str | None = None