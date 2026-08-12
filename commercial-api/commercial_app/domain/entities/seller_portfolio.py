from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SellerCustomerAssignment:
    customer_code: str
    customer_store: str
    customer_name: str | None = None


@dataclass(frozen=True, slots=True)
class SellerPortfolioMember:
    user_id: str
    role: str  # owner | member


@dataclass(frozen=True, slots=True)
class SellerPortfolio:
    id: str
    user_id: str
    display_name: str
    active: bool
    customers: tuple[SellerCustomerAssignment, ...]
    members: tuple[SellerPortfolioMember, ...] = ()

    @property
    def owner_user_id(self) -> str:
        for member in self.members:
            if member.role == "owner":
                return member.user_id
        return self.user_id
