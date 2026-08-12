"""Escopo de clientes por membership de carteira (regra do commercial-api)."""

from __future__ import annotations

from dataclasses import dataclass

from commercial_app.domain.entities.seller_portfolio import SellerPortfolio
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
    """None em allowed_customers = irrestrito (manage/team sem filtro)."""

    unrestricted: bool
    allowed_customers: frozenset[tuple[str, str]] | None
    empty_portfolio: bool = False
    message: str | None = None
    portfolio_id: str | None = None

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
    salvo escopo manage/team (irrestrito). Filtro opcional por PK da carteira
    (team/manage).
    """

    def __init__(self, repository: SellerPortfolioRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        user_id: str,
        unrestricted: bool,
        portfolio_id: str | None = None,
    ) -> CommercialCustomerScope:
        pid = (portfolio_id or "").strip() or None
        if pid:
            if not unrestricted:
                raise PermissionError(
                    SellerPortfolioMessagesContentService.error(
                        "portfolioFilterRequiresTeam"
                    )
                )
            return self._scope_from_portfolio_id(pid)

        if unrestricted:
            return CommercialCustomerScope(
                unrestricted=True,
                allowed_customers=None,
            )

        uid = (user_id or "").strip()
        if not uid:
            return CommercialCustomerScope(
                unrestricted=False,
                allowed_customers=frozenset(),
                empty_portfolio=True,
                message=SellerPortfolioMessagesContentService.error("emptyPortfolioLink"),
            )

        portfolios = self._repository.list_by_user_id(uid, active_only=True)
        if not portfolios:
            return CommercialCustomerScope(
                unrestricted=False,
                allowed_customers=frozenset(),
                empty_portfolio=True,
                message=SellerPortfolioMessagesContentService.error("emptyPortfolioLink"),
            )

        allowed = frozenset(
            _normalize_pair(item.customer_code, item.customer_store)
            for portfolio in portfolios
            for item in portfolio.customers
            if _normalize_pair(item.customer_code, item.customer_store)[0]
            and _normalize_pair(item.customer_code, item.customer_store)[1]
        )
        if not allowed:
            return CommercialCustomerScope(
                unrestricted=False,
                allowed_customers=frozenset(),
                empty_portfolio=True,
                portfolio_id=portfolios[0].id,
                message=SellerPortfolioMessagesContentService.error(
                    "emptyPortfolioCustomers"
                ),
            )
        return CommercialCustomerScope(
            unrestricted=False,
            allowed_customers=allowed,
            portfolio_id=portfolios[0].id,
        )

    def _scope_from_portfolio_id(self, portfolio_id: str) -> CommercialCustomerScope:
        portfolio = self._repository.get_by_id(portfolio_id)
        if portfolio is None:
            raise LookupError(
                SellerPortfolioMessagesContentService.error("portfolioNotFound")
            )
        if not portfolio.active:
            raise ValueError(
                SellerPortfolioMessagesContentService.error("portfolioInactiveFilter")
            )
        return self._scope_from_portfolio(portfolio)

    def _scope_from_portfolio(self, portfolio: SellerPortfolio) -> CommercialCustomerScope:
        allowed = frozenset(
            _normalize_pair(item.customer_code, item.customer_store)
            for item in portfolio.customers
            if _normalize_pair(item.customer_code, item.customer_store)[0]
            and _normalize_pair(item.customer_code, item.customer_store)[1]
        )
        if not allowed:
            return CommercialCustomerScope(
                unrestricted=False,
                allowed_customers=frozenset(),
                empty_portfolio=True,
                portfolio_id=portfolio.id,
                message=SellerPortfolioMessagesContentService.error(
                    "emptyPortfolioCustomers"
                ),
            )
        return CommercialCustomerScope(
            unrestricted=False,
            allowed_customers=allowed,
            portfolio_id=portfolio.id,
        )

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
