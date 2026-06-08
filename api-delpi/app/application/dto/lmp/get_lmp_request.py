# app/application/dto/lmp/get_lmp_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class GetLMPRequest:
    sale_number: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None