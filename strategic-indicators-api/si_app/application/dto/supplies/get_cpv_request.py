from dataclasses import dataclass, field
from typing import Optional, Sequence


@dataclass
class GetCPVRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    top_limit: int = 5
    cfops: Sequence[str] = field(default_factory=lambda: ("5101", "5124", "6101", "6124"))