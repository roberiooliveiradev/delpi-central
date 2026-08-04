from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence

from app.domain.ports.pedidos_venda_abertos.customer_enrichment_repository_port import (
    CustomerEnrichmentRepositoryPort,
)
from app.domain.services.pedidos_venda_abertos.billing_series_service import (
    BillingSeriesPoint,
    fill_billing_monthly_series,
    month_key_from_protheus,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


@dataclass(frozen=True, slots=True)
class ListCustomerBillingSeriesRequest:
    customers: Sequence[tuple[str, str]]
    months: int = 12


@dataclass(frozen=True, slots=True)
class CustomerBillingSeriesResult:
    points: list[BillingSeriesPoint]
    months: int
    customer_count: int

    def to_dict(self) -> dict:
        return {
            "months": self.months,
            "customer_count": self.customer_count,
            "points": [point.to_dict() for point in self.points],
        }


class ListCustomerBillingSeriesUseCase:
    MAX_CUSTOMERS = 200
    MAX_MONTHS = 24

    def __init__(self, enrichment_repository: CustomerEnrichmentRepositoryPort):
        self._enrichment_repository = enrichment_repository

    def execute(
        self, request: ListCustomerBillingSeriesRequest
    ) -> CustomerBillingSeriesResult:
        pairs: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for raw_code, raw_store in request.customers:
            code = (raw_code or "").strip()
            store = (raw_store or "").strip()
            if not code or not store:
                continue
            key = (code, store)
            if key in seen:
                continue
            seen.add(key)
            pairs.append(key)
            if len(pairs) >= self.MAX_CUSTOMERS:
                break

        months = max(1, min(int(request.months or 12), self.MAX_MONTHS))
        end = date.today()
        # Cobrir o mês mais antigo inteiro (≈ months*31 dias).
        start = end - timedelta(days=months * 31)

        if not pairs:
            return CustomerBillingSeriesResult(
                points=fill_billing_monthly_series(
                    billed_by_month={},
                    end=end,
                    months=months,
                ),
                months=months,
                customer_count=0,
            )

        qb = QueryBuilder()
        start_protheus = qb.convert_date_to_protheus(start.isoformat())
        end_protheus = qb.convert_date_to_protheus(end.isoformat())

        rows = self._enrichment_repository.fetch_billing_monthly_series(
            customers=pairs,
            start_date=start_protheus,
            end_date=end_protheus,
        )
        billed_by_month: dict[str, float] = {}
        for row in rows:
            key = month_key_from_protheus(row.year_month)
            if not key:
                continue
            billed_by_month[key] = billed_by_month.get(key, 0.0) + float(row.billed_value or 0.0)

        return CustomerBillingSeriesResult(
            points=fill_billing_monthly_series(
                billed_by_month=billed_by_month,
                end=end,
                months=months,
            ),
            months=months,
            customer_count=len(pairs),
        )
