# app/application/dto/commercial/get_rol_by_customer_request.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetRolByCustomerRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_codes: Optional[list[str]] = None
    limit: int = 20
    include_others: bool = True

    def validate(self) -> None:
        if not self.start_date or not self.end_date:
            raise ValueError("start_date e end_date são obrigatórios.")
        if int(self.limit) < 1 or int(self.limit) > 500:
            raise ValueError("limit deve estar entre 1 e 500.")
        if self.branch is not None and str(self.branch).strip() not in {"01", "02"}:
            raise ValueError("branch deve ser 01, 02 ou omitido (consolidado).")
