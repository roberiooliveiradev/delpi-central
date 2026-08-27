from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass
class GetSalesOrderOtdByCustomerRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_codes: Optional[list[str]] = None
    customer_names: Optional[list[str]] = None
    exclude_customer_codes: Optional[list[str]] = None
    exclude_customer_names: Optional[list[str]] = None
    page: int = 1
    page_size: int = 50

    def validate(self) -> None:
        if int(self.page) < 1:
            raise ValueError("page deve ser >= 1.")
        if int(self.page_size) < 1 or int(self.page_size) > 500:
            raise ValueError("page_size deve estar entre 1 e 500.")
        # all / omitido → consolidado (None); TV manda branch=all.
        self.branch = optional_concrete_branch(self.branch)
