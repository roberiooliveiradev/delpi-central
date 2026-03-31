from dataclasses import dataclass
from typing import Optional

@dataclass
class ProductionRequest:
    branch: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]

    