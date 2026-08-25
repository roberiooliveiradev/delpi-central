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
    customer_names: Optional[list[str]] = None
    exclude_customer_codes: Optional[list[str]] = None
    exclude_customer_names: Optional[list[str]] = None
    limit: int = 20
    include_others: bool = True
    page: int = 1
    page_size: Optional[int] = None

    def validate(self) -> None:
        if not self.start_date or not self.end_date:
            raise ValueError("start_date e end_date são obrigatórios.")
        if int(self.limit) < 1 or int(self.limit) > 500:
            raise ValueError("limit deve estar entre 1 e 500.")
        if self.branch is not None and str(self.branch).strip() not in {"01", "02"}:
            raise ValueError("branch deve ser 01, 02 ou omitido (consolidado).")
        if int(self.page) < 1:
            raise ValueError("page deve ser >= 1.")
        if self.page_size is not None and (
            int(self.page_size) < 1 or int(self.page_size) > 500
        ):
            raise ValueError("page_size deve estar entre 1 e 500.")
