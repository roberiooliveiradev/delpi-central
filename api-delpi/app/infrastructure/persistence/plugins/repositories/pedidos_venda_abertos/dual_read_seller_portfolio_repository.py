"""Leitura dual commercial + legado para carteiras PVA / Comercial.

Após `COMMERCIAL_PORTFOLIO_SOURCE=commercial`, o MFE lista carteiras no schema
`commercial`, mas a api-delpi ainda filtrava pedidos pelo schema legado
(`pedidos_venda_abertos.sellers`) — `seller_id` virava 404.
"""

from __future__ import annotations

from typing import Sequence

from app.domain.entities.pedidos_venda_abertos.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)
from app.domain.ports.pedidos_venda_abertos.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)


class DualReadSellerPortfolioRepository(SellerPortfolioRepositoryPort):
    """Lê commercial primeiro, fallback legado; writes no repositório ativo."""

    def __init__(
        self,
        *,
        commercial: SellerPortfolioRepositoryPort,
        legacy: SellerPortfolioRepositoryPort,
        write_source: str = "commercial",
    ) -> None:
        self._commercial = commercial
        self._legacy = legacy
        source = (write_source or "commercial").strip().lower()
        self._write = commercial if source == "commercial" else legacy

    def get_by_id(self, seller_id: str) -> SellerPortfolio | None:
        return self._commercial.get_by_id(seller_id) or self._legacy.get_by_id(seller_id)

    def get_by_user_id(self, user_id: str) -> SellerPortfolio | None:
        return self._commercial.get_by_user_id(user_id) or self._legacy.get_by_user_id(
            user_id
        )

    def list_by_user_id(
        self, user_id: str, *, active_only: bool = True
    ) -> list[SellerPortfolio]:
        commercial = self._commercial.list_by_user_id(user_id, active_only=active_only)
        if commercial:
            return commercial
        return self._legacy.list_by_user_id(user_id, active_only=active_only)

    def list_sellers(self, *, active_only: bool = False) -> list[SellerPortfolio]:
        primary = self._write.list_sellers(active_only=active_only)
        if primary:
            return primary
        fallback = self._commercial if self._write is self._legacy else self._legacy
        return fallback.list_sellers(active_only=active_only)

    def create_seller(
        self,
        *,
        user_id: str,
        display_name: str,
        created_by_user_id: str | None,
    ) -> SellerPortfolio:
        return self._write.create_seller(
            user_id=user_id,
            display_name=display_name,
            created_by_user_id=created_by_user_id,
        )

    def update_seller(
        self,
        *,
        seller_id: str,
        display_name: str | None = None,
        active: bool | None = None,
    ) -> SellerPortfolio | None:
        return self._write.update_seller(
            seller_id=seller_id,
            display_name=display_name,
            active=active,
        )

    def deactivate_seller(self, seller_id: str) -> SellerPortfolio | None:
        return self._write.deactivate_seller(seller_id)

    def replace_customers(
        self,
        *,
        seller_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> SellerPortfolio | None:
        return self._write.replace_customers(seller_id=seller_id, customers=customers)

    def add_customer(
        self,
        *,
        seller_id: str,
        customer: SellerCustomerAssignment,
    ) -> SellerPortfolio | None:
        return self._write.add_customer(seller_id=seller_id, customer=customer)

    def remove_customer(
        self,
        *,
        seller_id: str,
        customer_code: str,
        customer_store: str,
    ) -> SellerPortfolio | None:
        return self._write.remove_customer(
            seller_id=seller_id,
            customer_code=customer_code,
            customer_store=customer_store,
        )

    def transfer_customers(
        self,
        *,
        source_seller_id: str,
        target_seller_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> tuple[SellerPortfolio, SellerPortfolio] | None:
        return self._write.transfer_customers(
            source_seller_id=source_seller_id,
            target_seller_id=target_seller_id,
            customers=customers,
        )
