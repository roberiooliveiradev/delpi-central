from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from app.domain.entities.pedidos_venda_abertos.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)
from app.domain.ports.pedidos_venda_abertos.seller_portfolio_repository_port import (
    SellerPortfolioRepositoryPort,
)


def _normalize_code(value: str) -> str:
    return str(value or "").strip()


def customer_key(code: str, store: str) -> tuple[str, str]:
    return (_normalize_code(code), _normalize_code(store))


def portfolio_to_dict(portfolio: SellerPortfolio) -> dict[str, Any]:
    return {
        "id": portfolio.id,
        "user_id": portfolio.user_id,
        "display_name": portfolio.display_name,
        "active": portfolio.active,
        "customer_count": len(portfolio.customers),
        "customers": [
            {
                "customer_code": item.customer_code,
                "customer_store": item.customer_store,
                "customer_name": item.customer_name,
            }
            for item in portfolio.customers
        ],
    }


def parse_customer_assignments(raw: Sequence[dict[str, Any]] | None) -> list[SellerCustomerAssignment]:
    if not raw:
        return []
    parsed: list[SellerCustomerAssignment] = []
    seen: set[tuple[str, str]] = set()
    for item in raw:
        code = _normalize_code(str(item.get("customer_code") or item.get("codigo") or ""))
        store = _normalize_code(str(item.get("customer_store") or item.get("loja") or ""))
        if not code or not store:
            raise ValueError("Cada cliente precisa de customer_code e customer_store.")
        key = (code, store)
        if key in seen:
            continue
        seen.add(key)
        name_raw = item.get("customer_name") or item.get("nome")
        name = str(name_raw).strip() if name_raw else None
        parsed.append(
            SellerCustomerAssignment(
                customer_code=code,
                customer_store=store,
                customer_name=name or None,
            )
        )
    return parsed


@dataclass(frozen=True, slots=True)
class CreateSellerRequest:
    user_id: str
    display_name: str
    created_by_user_id: str | None = None
    customers: tuple[SellerCustomerAssignment, ...] = ()


class ManageSellerPortfolioUseCase:
    def __init__(self, repository: SellerPortfolioRepositoryPort):
        self._repository = repository

    def get_me(self, user_id: str) -> SellerPortfolio | None:
        return self._repository.get_by_user_id(user_id)

    def list_sellers(self, *, active_only: bool = False) -> list[SellerPortfolio]:
        return self._repository.list_sellers(active_only=active_only)

    def get_seller(self, seller_id: str) -> SellerPortfolio | None:
        return self._repository.get_by_id(seller_id)

    def create_seller(self, request: CreateSellerRequest) -> SellerPortfolio:
        user_id = _normalize_code(request.user_id)
        display_name = _normalize_code(request.display_name)
        if not user_id:
            raise ValueError("user_id é obrigatório.")
        if not display_name:
            raise ValueError("display_name é obrigatório.")
        existing = self._repository.get_by_user_id(user_id)
        if existing is not None:
            raise ValueError("Já existe vendedor cadastrado para este usuário.")
        portfolio = self._repository.create_seller(
            user_id=user_id,
            display_name=display_name,
            created_by_user_id=request.created_by_user_id,
        )
        if request.customers:
            updated = self._repository.replace_customers(
                seller_id=portfolio.id,
                customers=request.customers,
            )
            if updated is not None:
                return updated
        return portfolio

    def update_seller(
        self,
        *,
        seller_id: str,
        display_name: str | None = None,
        active: bool | None = None,
    ) -> SellerPortfolio:
        if display_name is not None and not _normalize_code(display_name):
            raise ValueError("display_name não pode ser vazio.")
        updated = self._repository.update_seller(
            seller_id=seller_id,
            display_name=_normalize_code(display_name) if display_name is not None else None,
            active=active,
        )
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        return updated

    def deactivate_seller(self, seller_id: str) -> SellerPortfolio:
        updated = self._repository.deactivate_seller(seller_id)
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        return updated

    def replace_customers(
        self,
        *,
        seller_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> SellerPortfolio:
        updated = self._repository.replace_customers(
            seller_id=seller_id,
            customers=customers,
        )
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        return updated

    def add_customer(
        self,
        *,
        seller_id: str,
        customer: SellerCustomerAssignment,
    ) -> SellerPortfolio:
        if not customer.customer_code or not customer.customer_store:
            raise ValueError("customer_code e customer_store são obrigatórios.")
        updated = self._repository.add_customer(seller_id=seller_id, customer=customer)
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        return updated

    def remove_customer(
        self,
        *,
        seller_id: str,
        customer_code: str,
        customer_store: str,
    ) -> SellerPortfolio:
        code, store = customer_key(customer_code, customer_store)
        if not code or not store:
            raise ValueError("customer_code e customer_store são obrigatórios.")
        updated = self._repository.remove_customer(
            seller_id=seller_id,
            customer_code=code,
            customer_store=store,
        )
        if updated is None:
            raise LookupError("Vendedor não encontrado.")
        return updated

    def transfer_customers(
        self,
        *,
        source_seller_id: str,
        target_seller_id: str,
        customers: Sequence[SellerCustomerAssignment],
    ) -> tuple[SellerPortfolio, SellerPortfolio]:
        source_id = _normalize_code(source_seller_id)
        target_id = _normalize_code(target_seller_id)
        if not source_id or not target_id:
            raise ValueError("Origem e destino da transferência são obrigatórios.")
        if source_id == target_id:
            raise ValueError("Origem e destino devem ser vendedores diferentes.")
        if not customers:
            raise ValueError("Selecione ao menos um cliente para transferir.")

        source = self._repository.get_by_id(source_id)
        if source is None:
            raise LookupError("Vendedor de origem não encontrado.")
        target = self._repository.get_by_id(target_id)
        if target is None:
            raise LookupError("Vendedor de destino não encontrado.")
        if not target.active:
            raise ValueError("Não é possível transferir para um vendedor inativo.")

        owned = {
            (item.customer_code, item.customer_store): item for item in source.customers
        }
        to_move: list[SellerCustomerAssignment] = []
        seen: set[tuple[str, str]] = set()
        for item in customers:
            key = customer_key(item.customer_code, item.customer_store)
            if not key[0] or not key[1]:
                raise ValueError("Cada cliente precisa de customer_code e customer_store.")
            if key in seen:
                continue
            seen.add(key)
            owned_item = owned.get(key)
            if owned_item is None:
                raise ValueError(
                    f"Cliente {key[0]}/{key[1]} não pertence à carteira de origem."
                )
            to_move.append(
                SellerCustomerAssignment(
                    customer_code=owned_item.customer_code,
                    customer_store=owned_item.customer_store,
                    customer_name=item.customer_name or owned_item.customer_name,
                )
            )

        result = self._repository.transfer_customers(
            source_seller_id=source_id,
            target_seller_id=target_id,
            customers=to_move,
        )
        if result is None:
            raise LookupError("Vendedor de origem ou destino não encontrado.")
        return result
