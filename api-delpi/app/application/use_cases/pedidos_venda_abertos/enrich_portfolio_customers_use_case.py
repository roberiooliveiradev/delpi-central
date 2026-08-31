from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Sequence

from app.application.use_cases.pedidos_venda_abertos.manage_customer_avatar_use_case import (
    ManageCustomerAvatarUseCase,
)
from app.domain.ports.pedidos_venda_abertos.customer_enrichment_repository_port import (
    CustomerEnrichmentRepositoryPort,
)
from app.domain.services.pedidos_venda_abertos.billing_trend_service import (
    BillingTrendDirection,
    clamp_billing_trend_window_days,
    resolve_billing_trend,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_billing_series_sql import (
    DEFAULT_BILLING_NATURE,
    SUPPORTED_BILLING_NATURES,
    normalize_billing_nature,
)
from app.infrastructure.persistence.totvs.query_builder import QueryBuilder


@dataclass(frozen=True, slots=True)
class CustomerEnrichmentItem:
    customer_code: str
    customer_store: str
    city: str | None
    state: str | None
    last_purchase_date: str | None
    billed_12m: float
    billed_recent_6m: float
    billed_prior_6m: float
    billing_trend: BillingTrendDirection
    billing_trend_pct: float | None
    has_avatar: bool
    contact_name: str | None = None
    phone: str | None = None
    email: str | None = None
    window_days: int = 30
    nature: str = DEFAULT_BILLING_NATURE

    def to_dict(self) -> dict:
        return {
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "city": self.city,
            "state": self.state,
            "last_purchase_date": self.last_purchase_date,
            "billed_12m": self.billed_12m,
            "billed_recent_6m": self.billed_recent_6m,
            "billed_prior_6m": self.billed_prior_6m,
            "billing_trend": self.billing_trend,
            "billing_trend_pct": self.billing_trend_pct,
            "has_avatar": self.has_avatar,
            "window_days": self.window_days,
            "nature": self.nature,
            "billingNature": self.nature,
            "supportedNatures": list(SUPPORTED_BILLING_NATURES),
            "avatar_url": (
                f"/pedidos-venda-abertos/customers/"
                f"{self.customer_code}/{self.customer_store}/avatar"
                if self.has_avatar
                else None
            ),
            "contact_name": self.contact_name,
            "phone": self.phone,
            "email": self.email,
        }


@dataclass(frozen=True, slots=True)
class EnrichCustomersRequest:
    customers: Sequence[tuple[str, str]]
    window_days: int | None = None
    nature: str | None = None


class EnrichPortfolioCustomersUseCase:
    MAX_CUSTOMERS = 200

    def __init__(
        self,
        enrichment_repository: CustomerEnrichmentRepositoryPort,
        avatar_use_case: ManageCustomerAvatarUseCase,
    ):
        self._enrichment_repository = enrichment_repository
        self._avatar_use_case = avatar_use_case

    def execute(self, request: EnrichCustomersRequest) -> list[CustomerEnrichmentItem]:
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

        if not pairs:
            return []

        window_days = clamp_billing_trend_window_days(request.window_days)
        nature = normalize_billing_nature(request.nature)
        end = date.today()
        mid = end - timedelta(days=window_days)
        start = end - timedelta(days=window_days * 2)
        qb = QueryBuilder()
        start_protheus = qb.convert_date_to_protheus(start.isoformat())
        mid_protheus = qb.convert_date_to_protheus(mid.isoformat())
        end_protheus = qb.convert_date_to_protheus(end.isoformat())

        geo = {
            (item.customer_code, item.customer_store): item
            for item in self._enrichment_repository.fetch_customer_geo(customers=pairs)
        }
        billing = {
            (item.customer_code, item.customer_store): item
            for item in self._enrichment_repository.fetch_billing_12m(
                customers=pairs,
                start_date=start_protheus,
                mid_date=mid_protheus,
                end_date=end_protheus,
                nature=nature,
            )
        }
        avatars = self._avatar_use_case.list_keys_with_avatar(customers=pairs)

        result: list[CustomerEnrichmentItem] = []
        for code, store in pairs:
            geo_item = geo.get((code, store))
            bill_item = billing.get((code, store))
            recent = float(bill_item.billed_recent_6m) if bill_item else 0.0
            prior = float(bill_item.billed_prior_6m) if bill_item else 0.0
            trend = resolve_billing_trend(
                billed_recent=recent,
                billed_prior=prior,
            )
            result.append(
                CustomerEnrichmentItem(
                    customer_code=code,
                    customer_store=store,
                    city=geo_item.city if geo_item else None,
                    state=geo_item.state if geo_item else None,
                    last_purchase_date=(
                        bill_item.last_purchase_date if bill_item else None
                    ),
                    billed_12m=float(bill_item.billed_12m) if bill_item else 0.0,
                    billed_recent_6m=recent,
                    billed_prior_6m=prior,
                    billing_trend=trend.direction,
                    billing_trend_pct=trend.change_pct,
                    has_avatar=(code, store) in avatars,
                    contact_name=geo_item.contact_name if geo_item else None,
                    phone=geo_item.phone if geo_item else None,
                    email=geo_item.email if geo_item else None,
                    window_days=window_days,
                    nature=nature,
                )
            )
        return result
