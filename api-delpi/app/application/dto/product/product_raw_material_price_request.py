from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductRawMaterialPriceRequest:
    code: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None
    history_limit: Optional[int] = None
