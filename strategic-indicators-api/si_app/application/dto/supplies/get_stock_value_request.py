from dataclasses import dataclass
from typing import Optional


@dataclass
class GetStockValueRequest:
    branch: Optional[str] = None
    location: Optional[str] = None
    top_limit: int = 10