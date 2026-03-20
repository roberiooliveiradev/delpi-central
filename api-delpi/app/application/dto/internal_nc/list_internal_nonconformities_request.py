from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class ListInternalNonconformitiesRequest:
    page: int = 1
    page_size: int = 20
    current_status: Optional[str] = None
    sector: Optional[str] = None
    search: Optional[str] = None