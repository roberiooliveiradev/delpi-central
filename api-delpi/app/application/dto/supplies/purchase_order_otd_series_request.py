from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch
ALLOWED_PURCHASE_ORDER_OTD_SERIES_GRANULARITIES = frozenset(
    {"day", "week", "month", "year"}
)


@dataclass
class PurchaseOrderOtdSeriesRequest:
    granularity: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None

    def validate(self) -> None:
        normalized = (self.granularity or "").strip().lower()
        if normalized not in ALLOWED_PURCHASE_ORDER_OTD_SERIES_GRANULARITIES:
            raise ValueError(
                "granularity inválida. Use day, week, month ou year."
            )
        self.granularity = normalized


    def __post_init__(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
