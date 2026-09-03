from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetRolByProductRequest:
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
    group_by: str = "product"
    limit: int = 500

    def validate(self) -> None:
        if not self.start_date or not self.end_date:
            raise ValueError("start_date e end_date são obrigatórios.")
        if int(self.limit) < 1 or int(self.limit) > 500:
            raise ValueError("limit deve estar entre 1 e 500.")
        if self.branch is not None and str(self.branch).strip() not in {"01", "02"}:
            raise ValueError("branch deve ser 01, 02 ou omitido (consolidado).")
        group = (self.group_by or "product").strip().lower()
        if group not in {"product", "product_group"}:
            raise ValueError("group_by deve ser product ou product_group.")
        self.group_by = group
        if self.market is not None:
            market = str(self.market).strip().lower()
            if market not in {"domestic", "export"}:
                raise ValueError("market deve ser domestic, export ou omitido.")
            self.market = market
