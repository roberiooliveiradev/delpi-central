from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.application.dto.commercial.sales_order_otd_series_request import (
    ALLOWED_SALES_ORDER_OTD_SERIES_GRANULARITIES,
)

DEFAULT_TOP_CUSTOMERS = 20
MAX_TOP_CUSTOMERS = 100
DEFAULT_GRANULARITY = "week"


@dataclass
class GetSalesOrderOtdSeriesByCustomerRequest:
    granularity: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_codes: Optional[list[str]] = None
    customer_names: Optional[list[str]] = None
    exclude_customer_codes: Optional[list[str]] = None
    exclude_customer_names: Optional[list[str]] = None
    page: int = 1
    page_size: int = 50
    top_customers: int = DEFAULT_TOP_CUSTOMERS

    def has_explicit_customer_filter(self) -> bool:
        return bool(self.customer_codes) or bool(self.customer_names)

    def validate(self) -> None:
        normalized = (self.granularity or DEFAULT_GRANULARITY).strip().lower()
        if normalized not in ALLOWED_SALES_ORDER_OTD_SERIES_GRANULARITIES:
            raise ValueError(
                "granularity inválida. Use day, week, month ou year."
            )
        self.granularity = normalized
        if int(self.page) < 1:
            raise ValueError("page deve ser >= 1.")
        if int(self.page_size) < 1 or int(self.page_size) > 500:
            raise ValueError("page_size deve estar entre 1 e 500.")
        if self.branch is not None and str(self.branch).strip() not in {"01", "02"}:
            raise ValueError("branch deve ser 01, 02 ou omitido (consolidado).")
        top = int(self.top_customers)
        if top < 1 or top > MAX_TOP_CUSTOMERS:
            raise ValueError(
                f"top_customers deve estar entre 1 e {MAX_TOP_CUSTOMERS}."
            )
        self.top_customers = top
