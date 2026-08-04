from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from app.domain.entities.pedidos_venda_abertos.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)


class SellerPortfolioRepositoryPort(ABC):
    """Persistência da carteira manual (Plugins Postgres)."""

    @abstractmethod
    def get_by_id(self, seller_id: str) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def list_sellers(self, *, active_only: bool = False) -> list[SellerPortfolio]:
        raise NotImplementedError

    @abstractmethod
    def create_seller(
        self,
        *,
        user_id: str,
        display_name: str,
        created_by_user_id: str | None,
    ) -> SellerPortfolio:
        raise NotImplementedError

    @abstractmethod
    def update_seller(
        self,
        *,
        seller_id: str,
        display_name: str | None = None,
        active: bool | None = None,
    ) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def deactivate_seller(self, seller_id: str) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def replace_customers(
        self,
        *,
        seller_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def add_customer(
        self,
        *,
        seller_id: str,
        customer: SellerCustomerAssignment,
    ) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def remove_customer(
        self,
        *,
        seller_id: str,
        customer_code: str,
        customer_store: str,
    ) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def transfer_customers(
        self,
        *,
        source_seller_id: str,
        target_seller_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> tuple[SellerPortfolio, SellerPortfolio] | None:
        """Move clientes da origem para o destino (atômico). None se origem/destino inexistentes."""
        raise NotImplementedError
