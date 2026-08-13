from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class CustomerGeoRow:
    customer_code: str
    customer_store: str
    city: str | None
    state: str | None
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None


@dataclass(frozen=True, slots=True)
class CustomerBilling12mRow:
    customer_code: str
    customer_store: str
    last_purchase_date: str | None
    billed_12m: float
    billed_recent_6m: float = 0.0
    billed_prior_6m: float = 0.0


@dataclass(frozen=True, slots=True)
class CustomerBillingMonthRow:
    """Agregado do bucket (YYYYMMDD / YYYYMM / YYYY Protheus) somando os clientes."""

    year_month: str
    billed_value: float


class CustomerEnrichmentRepositoryPort(ABC):
    @abstractmethod
    def fetch_customer_geo(
        self,
        *,
        customers: Sequence[tuple[str, str]],
    ) -> list[CustomerGeoRow]:
        raise NotImplementedError

    @abstractmethod
    def fetch_billing_12m(
        self,
        *,
        customers: Sequence[tuple[str, str]],
        start_date: str,
        mid_date: str,
        end_date: str,
    ) -> list[CustomerBilling12mRow]:
        raise NotImplementedError

    @abstractmethod
    def fetch_billing_monthly_series(
        self,
        *,
        customers: Sequence[tuple[str, str]],
        start_date: str,
        end_date: str,
        granularity: str = "month",
    ) -> list[CustomerBillingMonthRow]:
        raise NotImplementedError
