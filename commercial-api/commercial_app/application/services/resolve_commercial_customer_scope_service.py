"""Escopo de clientes por membership de carteira (regra do commercial-api)."""

from __future__ import annotations

from dataclasses import dataclass

from commercial_app.domain.ports.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)
from commercial_app.domain.services.seller_portfolio_messages_content_service import (
    SellerPortfolioMessagesContentService,
)


def _normalize_pair(code: str, store: str) -> tuple[str, str]:
    return (str(code or "").strip(), str(store or "").strip())


@dataclass(frozen=True, slots=True)
class CommercialCustomerScope:
    """None em allowed_customers = irrestrito (manage/team)."""

    unrestricted: bool
    allowed_customers: frozenset[tuple[str, str]] | None

    def allows(self, customer_code: str, customer_store: str) -> bool:
        if self.unrestricted:
            return True
        if self.allowed_customers is None:
            return True
        key = _normalize_pair(customer_code, customer_store)
        if not key[0] or not key[1]:
            return False
        return key in self.allowed_customers


class ResolveCommercialCustomerScopeService:
    """
    Fonte de verdade do Portal Comercial: só clientes das carteiras do usuário,
    salvo escopo manage/team (irrestrito).
    """

    def __init__(self, repository: SellerPortfolioRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        user_id: str,
        unrestricted: bool,
    ) -> CommercialCustomerScope:
        if unrestricted:
            return CommercialCustomerScope(unrestricted=True, allowed_customers=None)

        uid = (user_id or "").strip()
        if not uid:
            return CommercialCustomerScope(
                unrestricted=False,
                allowed_customers=frozenset(),
            )

        portfolios = self._repository.list_by_user_id(uid, active_only=True)
        allowed = frozenset(
            _normalize_pair(item.customer_code, item.customer_store)
            for portfolio in portfolios
            for item in portfolio.customers
            if _normalize_pair(item.customer_code, item.customer_store)[0]
            and _normalize_pair(item.customer_code, item.customer_store)[1]
        )
        return CommercialCustomerScope(unrestricted=False, allowed_customers=allowed)

    def filter_pairs(
        self,
        scope: CommercialCustomerScope,
        pairs: list[tuple[str, str]],
    ) -> list[tuple[str, str]]:
        if scope.unrestricted:
            return [
                _normalize_pair(code, store)
                for code, store in pairs
                if _normalize_pair(code, store)[0] and _normalize_pair(code, store)[1]
            ]
        return [
            key
            for code, store in pairs
            if (key := _normalize_pair(code, store))
            and key[0]
            and key[1]
            and scope.allows(key[0], key[1])
        ]

    def ensure_allows(
        self,
        scope: CommercialCustomerScope,
        *,
        customer_code: str,
        customer_store: str,
    ) -> None:
        if scope.allows(customer_code, customer_store):
            return
        raise LookupError(
            SellerPortfolioMessagesContentService.error("customerOutsidePortfolio")
        )
