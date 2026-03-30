# app/application/dto/financial/get_rol_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class GetRolRequest:
    branch: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None