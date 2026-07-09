from dataclasses import dataclass
from typing import Optional

ALLOWED_SALES_ORDER_OTD_SERIES_GRANULARITIES = frozenset({"day", "week", "month", "year"})


@dataclass
class SalesOrderOtdSeriesRequest:
    granularity: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None
    customer_segment: Optional[str] = None

    def validate(self) -> None:
        normalized = (self.granularity or "").strip().lower()
        if normalized not in ALLOWED_SALES_ORDER_OTD_SERIES_GRANULARITIES:
            raise ValueError(
                "granularity inválida. Use day, week, month ou year."
            )
        self.granularity = normalized
