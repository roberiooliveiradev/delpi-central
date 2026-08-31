from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence

from app.application.shared.chart_period_buckets import (
    PeriodBucket,
    build_period_buckets,
)
from app.domain.ports.pedidos_venda_abertos.customer_enrichment_repository_port import (
    CustomerEnrichmentRepositoryPort,
)
from app.domain.services.pedidos_venda_abertos.billing_series_service import (
    BillingSeriesPoint,
    period_key_from_protheus,
    period_key_to_date,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_billing_series_sql import (
    BILLING_SERIES_GRANULARITIES,
    DEFAULT_BILLING_NATURE,
    SUPPORTED_BILLING_NATURES,
    normalize_billing_nature,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder

MAX_SPAN_DAYS = {
    "day": 93,
    "week": 366,
    "month": 744,
    "year": 3660,
}


@dataclass(frozen=True, slots=True)
class ListCustomerBillingSeriesRequest:
    customers: Sequence[tuple[str, str]]
    months: int = 12
    start_date: str | None = None
    end_date: str | None = None
    granularity: str | None = None
    nature: str | None = None


@dataclass(frozen=True, slots=True)
class CustomerBillingSeriesResult:
    points: list[BillingSeriesPoint]
    months: int
    customer_count: int
    granularity: str
    start_date: str
    end_date: str
    nature: str = DEFAULT_BILLING_NATURE

    def to_dict(self) -> dict:
        return {
            "months": self.months,
            "customer_count": self.customer_count,
            "granularity": self.granularity,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "nature": self.nature,
            "billingNature": self.nature,
            "supportedNatures": list(SUPPORTED_BILLING_NATURES),
            "points": [point.to_dict() for point in self.points],
        }


def _parse_iso_date(value: str | None) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("Data inválida. Use YYYY-MM-DD.") from exc


def _shift_month(anchor: date, *, months_back: int) -> date:
    year = anchor.year
    month = anchor.month - months_back
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def _match_bucket_key(period_key: str, buckets: Sequence[PeriodBucket]) -> str | None:
    for bucket in buckets:
        if bucket.key == period_key:
            return bucket.key
    point_date = period_key_to_date(period_key)
    if point_date is None:
        return None
    iso = point_date.isoformat()
    for bucket in buckets:
        if bucket.start_date <= iso <= bucket.end_date:
            return bucket.key
    return None


class ListCustomerBillingSeriesUseCase:
    MAX_CUSTOMERS = 200
    MAX_MONTHS = 24

    def __init__(self, enrichment_repository: CustomerEnrichmentRepositoryPort):
        self._enrichment_repository = enrichment_repository

    def _resolve_window(
        self, request: ListCustomerBillingSeriesRequest
    ) -> tuple[date, date, str, int]:
        grain = (request.granularity or "month").strip().lower() or "month"
        if grain not in BILLING_SERIES_GRANULARITIES:
            raise ValueError("granularity inválida. Use day, week, month ou year.")

        start = _parse_iso_date(request.start_date)
        end = _parse_iso_date(request.end_date)
        months = max(1, min(int(request.months or 12), self.MAX_MONTHS))

        if (start is None) ^ (end is None):
            raise ValueError("Informe start_date e end_date juntos.")
        if start and end and start > end:
            raise ValueError("start_date não pode ser posterior a end_date.")
        if start is None or end is None:
            end = date.today()
            start = _shift_month(end, months_back=months - 1)

        span_days = (end - start).days + 1
        max_span = MAX_SPAN_DAYS[grain]
        if span_days > max_span:
            raise ValueError(
                f"Período excede o limite de {max_span} dia(s) para granularidade {grain}."
            )
        return start, end, grain, months

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

        start, end, grain, months = self._resolve_window(request)
        nature = normalize_billing_nature(request.nature)
        buckets = build_period_buckets(
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            granularity=grain,
        ).buckets

        billed_by_key: dict[str, float] = {}
        if pairs:
            qb = QueryBuilder()
            start_protheus = qb.convert_date_to_protheus(start.isoformat())
            end_protheus = qb.convert_date_to_protheus(end.isoformat())
            rows = self._enrichment_repository.fetch_billing_monthly_series(
                customers=pairs,
                start_date=start_protheus,
                end_date=end_protheus,
                granularity=grain,
                nature=nature,
            )
            for row in rows:
                period_key = period_key_from_protheus(
                    row.year_month, granularity=grain
                )
                if not period_key:
                    continue
                bucket_key = _match_bucket_key(period_key, buckets)
                if not bucket_key:
                    continue
                billed_by_key[bucket_key] = billed_by_key.get(bucket_key, 0.0) + float(
                    row.billed_value or 0.0
                )

        points = [
            BillingSeriesPoint(
                month=bucket.key,
                label=bucket.label,
                value=float(billed_by_key.get(bucket.key, 0.0) or 0.0),
                date_start=bucket.start_date,
                date_end=bucket.end_date,
            )
            for bucket in buckets
        ]
        return CustomerBillingSeriesResult(
            points=points,
            months=months,
            customer_count=len(pairs),
            granularity=grain,
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            nature=nature,
        )
