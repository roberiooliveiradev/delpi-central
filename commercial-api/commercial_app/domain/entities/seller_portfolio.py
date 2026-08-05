from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SellerCustomerAssignment:
    customer_code: str
    customer_store: str
    customer_name: str | None = None


@dataclass(frozen=True, slots=True)
class SellerPortfolio:
    id: str
    user_id: str
    display_name: str
    active: bool
    customers: tuple[SellerCustomerAssignment, ...]
