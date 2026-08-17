from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
    SellerPortfolioMember,
)


class SellerPortfolioRepositoryPort(ABC):
    @abstractmethod
    def get_by_id(self, portfolio_id: str) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> SellerPortfolio | None:
        """Compat 1:1 — primeira carteira ativa do usuário (preferir list_by_user_id)."""
        raise NotImplementedError

    @abstractmethod
    def list_by_user_id(self, user_id: str, *, active_only: bool = True) -> list[SellerPortfolio]:
        raise NotImplementedError

    @abstractmethod
    def list_member_user_ids(self, *, active_portfolios_only: bool = True) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def list_portfolios(self, *, active_only: bool = False) -> list[SellerPortfolio]:
        raise NotImplementedError

    @abstractmethod
    def create_portfolio(
        self,
        *,
        user_id: str | None,
        display_name: str,
        created_by_user_id: str | None,
        member_user_ids: Sequence[str] | None = None,
    ) -> SellerPortfolio:
        raise NotImplementedError

    @abstractmethod
    def update_portfolio(
        self,
        *,
        portfolio_id: str,
        display_name: str | None = None,
        active: bool | None = None,
    ) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def deactivate_portfolio(self, portfolio_id: str) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def delete_portfolio(self, portfolio_id: str) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def replace_customers(
        self,
        *,
        portfolio_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def add_customer(
        self,
        *,
        portfolio_id: str,
        customer: SellerCustomerAssignment,
    ) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def remove_customer(
        self,
        *,
        portfolio_id: str,
        customer_code: str,
        customer_store: str,
    ) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def transfer_customers(
        self,
        *,
        source_portfolio_id: str,
        target_portfolio_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> tuple[SellerPortfolio, SellerPortfolio] | None:
        raise NotImplementedError

    @abstractmethod
    def replace_members(
        self,
        *,
        portfolio_id: str,
        members: Sequence[SellerPortfolioMember],
    ) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def add_member(
        self,
        *,
        portfolio_id: str,
        user_id: str,
        role: str = "member",
    ) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def remove_member(
        self,
        *,
        portfolio_id: str,
        user_id: str,
    ) -> SellerPortfolio | None:
        raise NotImplementedError

    @abstractmethod
    def set_owner(
        self,
        *,
        portfolio_id: str,
        user_id: str,
    ) -> SellerPortfolio | None:
        raise NotImplementedError
