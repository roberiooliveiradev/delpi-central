"""Port — matriz de faturamento por cliente × mês."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from app.application.dto.commercial.get_billing_by_customer_month_request import (
    GetBillingByCustomerMonthRequest,
)


class CommercialBillingByCustomerMonthRepositoryPort(ABC):
    @abstractmethod
    def list_billing_rows(
        self,
        request: GetBillingByCustomerMonthRequest,
    ) -> Sequence[dict]:
        """Linhas cruas: customer_code, customer_store, customer_name, year_month, billed_value."""
