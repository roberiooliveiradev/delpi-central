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
    """True = admin/gerente sem filtro (ou api-delpi.access)."""

    seller_id: str | None
    """Quando admin filtra um vendedor específico."""

    allowed_customers: frozenset[tuple[str, str]] | None
    """Pares (codigo, loja). None só quando unrestricted. frozenset vazio = sem carteira."""

    empty_portfolio: bool
    """Usuário sem vínculo / carteira vazia → dataset vazio com aviso."""

    message: str | None = None


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

        portfolio: SellerPortfolio | None
        if is_unrestricted and seller_filter:
            # Aceita id da carteira (PK) ou user_id (legado / callers equivocados).
            portfolio = self._repository.get_by_id(seller_filter)
            if portfolio is None:
                portfolio = self._repository.get_by_user_id(seller_filter)
            if portfolio is None:
                raise LookupError("Vendedor não encontrado para filtro de carteira.")
            if not portfolio.active:
                raise ValueError("Vendedor inativo não pode ser usado como filtro.")
        else:
            portfolio = self._repository.get_by_user_id(user_id)

        if portfolio is None or not portfolio.active:
            return PortfolioScope(
                unrestricted=False,
                seller_id=None,
                allowed_customers=frozenset(),
                empty_portfolio=True,
                message=(
                    "Nenhuma carteira de clientes cadastrada para o seu usuário. "
                    "Peça ao gerente para vincular seus clientes na Configuração."
                ),
            )

        allowed = frozenset(
            (item.customer_code, item.customer_store) for item in portfolio.customers
        )
        if not allowed:
            return PortfolioScope(
                unrestricted=False,
                seller_id=portfolio.id,
                allowed_customers=frozenset(),
                empty_portfolio=True,
                message="Sua carteira ainda não possui clientes vinculados.",
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
