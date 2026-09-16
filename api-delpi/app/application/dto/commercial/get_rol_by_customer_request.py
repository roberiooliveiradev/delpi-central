from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch


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
    product_codes: Optional[list[str]] = None
    product_groups: Optional[list[str]] = None
    market: Optional[str] = None
    limit: int = 20
    include_others: bool = True
    page: int = 1
    page_size: Optional[int] = None

    def validate(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
        if not self.start_date or not self.end_date:
            raise ValueError("start_date e end_date são obrigatórios.")
        if int(self.limit) < 1 or int(self.limit) > 500:
            raise ValueError("limit deve estar entre 1 e 500.")
        if int(self.page) < 1:
            raise ValueError("page deve ser >= 1.")
        if self.page_size is not None and (
            int(self.page_size) < 1 or int(self.page_size) > 500
        ):
            raise ValueError("page_size deve estar entre 1 e 500.")
        if self.market is not None:
            market = str(self.market).strip().lower()
            if market not in {"domestic", "export"}:
                raise ValueError("market deve ser domestic, export ou omitido.")
            self.market = market
