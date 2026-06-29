from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchCustomersRequest:
    code: Optional[str] = None
    name: Optional[str] = None
    store: Optional[str] = None
    page: int = 1
    page_size: int = 20
