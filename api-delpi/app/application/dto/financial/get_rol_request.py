# app/application/dto/financial/get_rol_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class GetRolRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None