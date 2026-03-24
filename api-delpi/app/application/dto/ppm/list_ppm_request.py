# app/application/dto/ppm/list_ppm_request.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class ListPpmRequest:
    type: str                   # internal | external
    branch: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    page: Optional[int] = None
    page_size: Optional[int] = None