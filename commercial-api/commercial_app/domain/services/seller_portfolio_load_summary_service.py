from __future__ import annotations

from collections import defaultdict
from typing import Sequence

from commercial_app.domain.entities.portfolio_load import (
    PersonLoadItem,
    PortfolioLoadItem,
    PortfolioLoadSummary,
    TotvsLoadMetricsStatus,
)
from commercial_app.domain.entities.seller_portfolio import SellerPortfolio
from commercial_app.domain.services.seller_portfolio_coverage_audit_service import (
    customer_coverage_key,
)

_TOTVS_UNAVAILABLE_REASON = "open_orders_aggregation_not_wired"


def _normalize(value: str) -> str:
    return str(value or "").strip()


def _member_ids(portfolio: SellerPortfolio) -> list[str]:
    from_members = [
        _normalize(member.user_id)
        for member in portfolio.members
        if _normalize(member.user_id)
    ]
    if from_members:
        # Preserva ordem de members; dedupe estável.
        seen: set[str] = set()
        ordered: list[str] = []
        for user_id in from_members:
            if user_id in seen:
                continue
            seen.add(user_id)
            ordered.append(user_id)
        return ordered
    owner = _normalize(portfolio.owner_user_id)
    return [owner] if owner else []


def _unique_customer_count(portfolio: SellerPortfolio) -> int:
    seen: set[tuple[str, str]] = set()
    for customer in portfolio.customers:
        key = customer_coverage_key(customer.customer_code, customer.customer_store)
        if not key[0] or not key[1]:
            continue
        seen.add(key)
    return len(seen)


class SellerPortfolioLoadSummaryService:
    """KPIs de carga por carteira e por pessoa (E6.2).

    customer_count / member_count vêm do estado Delpi (Postgres).
    open_value / attention_count ficam null enquanto a agregação TOTVS
    não estiver ligada (evita N+1 pesado no MFE).
    """

    def summarize(
        self,
        portfolios: Sequence[SellerPortfolio],
    ) -> PortfolioLoadSummary:
        portfolio_items: list[PortfolioLoadItem] = []
        by_user_portfolios: dict[str, list[SellerPortfolio]] = defaultdict(list)

        for portfolio in portfolios:
            member_ids = _member_ids(portfolio)
            portfolio_items.append(
                PortfolioLoadItem(
                    id=portfolio.id,
                    display_name=portfolio.display_name,
                    active=portfolio.active,
                    customer_count=_unique_customer_count(portfolio),
                    member_count=len(member_ids),
                    open_value=None,
                    attention_count=None,
                )
            )
            for user_id in member_ids:
                by_user_portfolios[user_id].append(portfolio)

        person_items: list[PersonLoadItem] = []
        for user_id in sorted(by_user_portfolios.keys()):
            person_portfolios = by_user_portfolios[user_id]
            customer_keys: set[tuple[str, str]] = set()
            portfolio_ids: list[str] = []
            for portfolio in person_portfolios:
                portfolio_ids.append(portfolio.id)
                for customer in portfolio.customers:
                    key = customer_coverage_key(
                        customer.customer_code,
                        customer.customer_store,
                    )
                    if key[0] and key[1]:
                        customer_keys.add(key)
            person_items.append(
                PersonLoadItem(
                    user_id=user_id,
                    portfolio_ids=tuple(portfolio_ids),
                    portfolio_count=len(portfolio_ids),
                    customer_count=len(customer_keys),
                    open_value=None,
                    attention_count=None,
                )
            )

        return PortfolioLoadSummary(
            portfolios=tuple(portfolio_items),
            by_person=tuple(person_items),
            totvs_metrics=TotvsLoadMetricsStatus(
                available=False,
                reason=_TOTVS_UNAVAILABLE_REASON,
            ),
        )
