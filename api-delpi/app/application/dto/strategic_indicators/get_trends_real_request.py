from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GetStrategicIndicatorsTrendsRealRequest:
    competence: str | None = None
    months: int = 6