from dataclasses import dataclass
from typing import Optional

ALLOWED_OEE_SERIES_GRANULARITIES = frozenset({"day", "week", "month", "year"})


@dataclass
class ProductionOeeSeriesRequest:
    granularity: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None

    def validate(self) -> None:
        normalized = (self.granularity or "").strip().lower()
        if normalized not in ALLOWED_OEE_SERIES_GRANULARITIES:
            raise ValueError("granularity deve ser day, week, month ou year.")
        self.granularity = normalized

        if self.branch is not None:
            branch = self.branch.strip()
            if branch and len(branch) != 2:
                raise ValueError("branch deve ter 2 caracteres.")
            self.branch = branch or None
