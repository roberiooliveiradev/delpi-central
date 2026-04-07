from __future__ import annotations

from dataclasses import dataclass

@dataclass
class GetExecutiveSummaryRealRequest:
    start_date: str | None = None
    end_date: str | None = None
    competence: str | None = None