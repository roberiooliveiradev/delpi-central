# app/domain/entities/lmp/lmp.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class LMP:
    sale_number: str
    sale_description: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    qtd_pi: Optional[int] = None