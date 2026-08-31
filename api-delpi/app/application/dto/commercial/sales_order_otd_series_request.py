from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch

ALLOWED_SALES_ORDER_OTD_SERIES_GRANULARITIES = frozenset({"day", "week", "month", "year"})


@dataclass
class SalesOrderOtdSeriesRequest:
    granularity: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_codes: Optional[list[str]] = None
    customer_code_stores: Optional[list[tuple[str, str]]] = None
    customer_names: Optional[list[str]] = None
    exclude_customer_codes: Optional[list[str]] = None
    exclude_customer_names: Optional[list[str]] = None

    def validate(self) -> None:
        normalized = (self.granularity or "").strip().lower()
        if normalized not in ALLOWED_SALES_ORDER_OTD_SERIES_GRANULARITIES:
            raise ValueError(
                "granularity inválida. Use day, week, month ou year."
            )
        self.granularity = normalized
        self.branch = optional_concrete_branch(self.branch)
