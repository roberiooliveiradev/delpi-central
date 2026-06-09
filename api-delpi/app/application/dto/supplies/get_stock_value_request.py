from dataclasses import dataclass
from typing import Optional


@dataclass
class GetStockValueRequest:
    branch: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    top_limit: int = 10
    summary_only: bool = False

    @property
    def uses_historical_estimation(self) -> bool:
        return bool(self.start_date or self.end_date)
