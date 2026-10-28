"""Request — matriz de faturamento por cliente × mês (gross NF ou net ROL)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.totvs.protheus_branches import optional_concrete_branch
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_billing_series_sql import (
    DEFAULT_BILLING_NATURE,
    normalize_billing_nature,
)


@dataclass
class GetBillingByCustomerMonthRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_codes: Optional[list[str]] = None
    customer_names: Optional[list[str]] = None
    exclude_customer_codes: Optional[list[str]] = None
    exclude_customer_names: Optional[list[str]] = None
    customer_centers: Optional[list[str]] = None
    nature: str = DEFAULT_BILLING_NATURE
    limit: int = 5000

    def validate(self) -> None:
        self.branch = optional_concrete_branch(self.branch)
        if not self.start_date or not self.end_date:
            raise ValueError("start_date e end_date são obrigatórios.")
        self.nature = normalize_billing_nature(self.nature)
        if int(self.limit) < 1 or int(self.limit) > 5000:
            raise ValueError("limit deve estar entre 1 e 5000.")
