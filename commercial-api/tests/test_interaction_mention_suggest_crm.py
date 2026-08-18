from __future__ import annotations

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    ResolveCommercialCustomerScopeService,
)
from commercial_app.application.use_cases.suggest_interaction_mentions import (
    SuggestInteractionMentionsUseCase,
)
from commercial_app.domain.entities.seller_portfolio import (
    SellerCustomerAssignment,
    SellerPortfolio,
)


class _Directory:
    def search_directory_users(self, *, query=None, limit=20, browse=False):
        return []


class _Gateway:
    def __init__(self, *, customers=None, orders=None, fail=False) -> None:
        self._customers = customers or {"data": {"items": []}}
        self._orders = orders or {"data": {"items": []}}
        self._fail = fail

    def search_active_customers(self, *, params=None):
        if self._fail:
            raise RuntimeError("api-delpi down")
        return self._customers

    def list_open_orders(self, *, params=None):
        if self._fail:
            raise RuntimeError("api-delpi down")
        return self._orders


class _Portfolios:
    def __init__(self, items: list[SellerPortfolio]) -> None:
        self._items = items

    def list_by_user_id(self, user_id: str, *, active_only: bool = True):
        return [item for item in self._items if item.user_id == user_id or any(
            member.user_id == user_id for member in item.members
        )]

    def list_portfolios(self, *, active_only: bool = False):
        return list(self._items)

    def get_by_id(self, portfolio_id: str):
        return next((item for item in self._items if item.id == portfolio_id), None)

    def get_by_user_id(self, user_id: str):
        found = self.list_by_user_id(user_id)
        return found[0] if found else None


def _portfolio() -> SellerPortfolio:
    return SellerPortfolio(
        id="p1",
        user_id="u1",
        display_name="Carteira Sul",
        active=True,
        customers=(
            SellerCustomerAssignment(
                customer_code="0001",
                customer_store="01",
                customer_name="WEG",
            ),
        ),
        members=(),
    )


def _use_case(*, gateway=None, portfolios=None) -> SuggestInteractionMentionsUseCase:
    repo = portfolios or _Portfolios([_portfolio()])
    return SuggestInteractionMentionsUseCase(
        _Directory(),
        portfolios=repo,
        scope=ResolveCommercialCustomerScopeService(repo),
        gateway=gateway or _Gateway(),
    )


def test_suggest_customer_respects_membership() -> None:
    gateway = _Gateway(
        customers={
            "data": {
                "items": [
                    {"code": "0001", "store": "01", "name": "WEG"},
                    {"code": "9999", "store": "01", "name": "Fora"},
                ]
            }
        }
    )
    items = _use_case(gateway=gateway).suggest(
        query="weg",
        kinds=["customer"],
        actor_user_id="u1",
    )
    assert [item["ref"]["customer_code"] for item in items] == ["0001"]
    assert items[0]["kind"] == "customer"


def test_suggest_customer_out_of_scope_is_empty_not_error() -> None:
    gateway = _Gateway(
        customers={"data": {"items": [{"code": "9999", "store": "01", "name": "Fora"}]}}
    )
    items = _use_case(gateway=gateway).suggest(
        query="fora",
        kinds=["customer"],
        actor_user_id="u1",
    )
    assert items == []


def test_suggest_crm_gateway_failure_returns_empty() -> None:
    items = _use_case(gateway=_Gateway(fail=True)).suggest(
        query="weg",
        kinds=["customer", "order"],
        actor_user_id="u1",
    )
    assert items == []


def test_suggest_portfolio_by_name() -> None:
    items = _use_case().suggest(
        query="sul",
        kinds=["portfolio"],
        actor_user_id="u1",
    )
    assert items[0]["kind"] == "portfolio"
    assert items[0]["ref"]["portfolio_id"] == "p1"


def test_suggest_order_filters_by_membership() -> None:
    gateway = _Gateway(
        orders={
            "data": {
                "items": [
                    {
                        "filial": "01",
                        "pedido": "102942",
                        "codigo_cadastro": "0001",
                        "loja_cadastro": "01",
                        "nome_cliente": "WEG",
                    },
                    {
                        "filial": "01",
                        "pedido": "1",
                        "codigo_cadastro": "9999",
                        "loja_cadastro": "01",
                        "nome_cliente": "Fora",
                    },
                ]
            }
        }
    )
    items = _use_case(gateway=gateway).suggest(
        query="102942",
        kinds=["order"],
        actor_user_id="u1",
    )
    assert len(items) == 1
    assert items[0]["ref"] == {"branch": "01", "order": "102942"}
