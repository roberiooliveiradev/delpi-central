from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Audit5S:
    id: str
    date: Optional[str]
    average_line_score: Optional[float]
    evaluated_area: Optional[str]
    auditor: Optional[str]
    audited: Optional[str]
    inspection_number: Optional[str]
    shift: Optional[str]
    branch: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)