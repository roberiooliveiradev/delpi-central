# app/application/dto/lmp/list_lmp_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class ListLMPRequest:
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None
    listing_type: Optional[str] = None
    page: Optional[int] = None
    page_size: Optional[int] = None