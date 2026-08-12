from __future__ import annotations

from dataclasses import dataclass

from app.domain.entities.pedidos_venda_abertos.seller_portfolio import SellerPortfolio
from app.domain.ports.pedidos_venda_abertos.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)


@dataclass(frozen=True, slots=True)
class PortfolioScope:
    """Escopo de carteira aplicado às consultas operacionais."""

    unrestricted: bool
    """True = manage canônico sem filtro de membership."""

    seller_id: str | None
    """Quando admin filtra um vendedor específico."""

    allowed_customers: frozenset[tuple[str, str]] | None
    """Pares (codigo, loja). None só quando unrestricted. frozenset vazio = sem carteira."""

    empty_portfolio: bool
    """Usuário sem vínculo / carteira vazia → dataset vazio com aviso."""

    message: str | None = None


_EMPTY_LINK_MESSAGE = (
    "Nenhuma carteira de clientes cadastrada para o seu usuário. "
    "Peça ao gerente para vincular seus clientes na Configuração."
)
_EMPTY_CUSTOMERS_MESSAGE = "Sua carteira ainda não possui clientes vinculados."


class ResolvePortfolioScopeUseCase:
    def __init__(self, repository: SellerPortfolioRepositoryPort):
        self._repository = repository

    def execute(
        self,
        *,
        user_id: str,
        is_unrestricted: bool,
        seller_id_filter: str | None = None,
    ) -> PortfolioScope:
        seller_filter = (seller_id_filter or "").strip() or None

        if is_unrestricted and not seller_filter:
            return PortfolioScope(
                unrestricted=True,
                seller_id=None,
                allowed_customers=None,
                empty_portfolio=False,
                message=None,
            )

        if is_unrestricted and seller_filter:
            return self._scope_from_seller_filter(seller_filter)

        return self._scope_from_user_membership(user_id)

    def _scope_from_seller_filter(self, seller_filter: str) -> PortfolioScope:
        # Aceita id da carteira (PK) ou user_id (legado / callers equivocados).
        portfolio = self._repository.get_by_id(seller_filter)
        if portfolio is None:
            portfolio = self._repository.get_by_user_id(seller_filter)
        if portfolio is None:
            raise LookupError("Vendedor não encontrado para filtro de carteira.")
        if not portfolio.active:
            raise ValueError("Vendedor inativo não pode ser usado como filtro.")
        return self._scope_from_portfolio(portfolio)

    def _scope_from_user_membership(self, user_id: str) -> PortfolioScope:
        portfolios = self._repository.list_by_user_id(user_id, active_only=True)
        if not portfolios:
            return PortfolioScope(
                unrestricted=False,
                seller_id=None,
                allowed_customers=frozenset(),
                empty_portfolio=True,
                message=_EMPTY_LINK_MESSAGE,
            )

        allowed = frozenset(
            (item.customer_code, item.customer_store)
            for portfolio in portfolios
            for item in portfolio.customers
        )
        if not allowed:
            return PortfolioScope(
                unrestricted=False,
                seller_id=portfolios[0].id,
                allowed_customers=frozenset(),
                empty_portfolio=True,
                message=_EMPTY_CUSTOMERS_MESSAGE,
            )

        return PortfolioScope(
            unrestricted=False,
            seller_id=portfolios[0].id,
            allowed_customers=allowed,
            empty_portfolio=False,
            message=None,
        )

    def _scope_from_portfolio(self, portfolio: SellerPortfolio) -> PortfolioScope:
        allowed = frozenset(
            (item.customer_code, item.customer_store) for item in portfolio.customers
        )
        if not allowed:
            return PortfolioScope(
                unrestricted=False,
                seller_id=portfolio.id,
                allowed_customers=frozenset(),
                empty_portfolio=True,
                message=_EMPTY_CUSTOMERS_MESSAGE,
            )
        return PortfolioScope(
            unrestricted=False,
            seller_id=portfolio.id,
            allowed_customers=allowed,
            empty_portfolio=False,
            message=None,
        )

    def customer_allowed(
        self,
        scope: PortfolioScope,
        *,
        customer_code: str,
        customer_store: str,
    ) -> bool:
        if scope.unrestricted:
            return True
        if scope.allowed_customers is None:
            return True
        key = (str(customer_code or "").strip(), str(customer_store or "").strip())
        return key in scope.allowed_customers
