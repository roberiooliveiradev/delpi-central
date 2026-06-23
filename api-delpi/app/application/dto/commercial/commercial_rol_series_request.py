from dataclasses import dataclass
from typing import Optional


ALLOWED_ROL_SERIES_GRANULARITIES = frozenset({"day", "week", "month", "year"})


@dataclass
class CommercialRolSeriesRequest:
    granularity: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    customer_segment: Optional[str] = None

    def validate(self) -> None:
        normalized = (self.granularity or "").strip().lower()
        if normalized not in ALLOWED_ROL_SERIES_GRANULARITIES:
            raise ValueError(
                "granularity deve ser day, week, month ou year."
            )
        self.granularity = normalized
