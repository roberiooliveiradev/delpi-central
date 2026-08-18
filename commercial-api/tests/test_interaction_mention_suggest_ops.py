from __future__ import annotations

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    ResolveCommercialCustomerScopeService,
)
from commercial_app.application.use_cases.suggest_interaction_mentions import (
    SuggestInteractionMentionsUseCase,
)
from tests.test_interaction_mention_suggest_crm import _Portfolios, _portfolio


class _Directory:
    def search_directory_users(self, *, query=None, limit=20, browse=False):
        return []


class _OpsGateway:
    def __init__(self) -> None:
        self.product_calls: list[str] = []
        self.fail_search = False

    def search_active_customers(self, *, params=None):
        return {"data": {"items": []}}

    def list_open_orders(self, *, params=None):
        return {"data": {"items": []}}

    def get_product(self, path, *, params=None):
        self.product_calls.append(path)
        if path == "/search":
            if self.fail_search:
                raise RuntimeError("no public search")
            return {
                "data": {
                    "items": [
                        {"code": "90AAAA01", "description": "Tampa"},
                    ]
                }
            }
        if path.endswith("/factory-status"):
            return {"data": {"product_code": "90AAAA01", "description": "Tampa"}}
        raise RuntimeError("not found")

    def get_production(self, path, *, params=None):
        if "/orders/by-op/" in path:
            return {"data": {"op": "00118901001", "branch": "01"}}
        raise RuntimeError("not found")

    def get_commercial_analytics(self, path, *, params=None):
        if path == "/proposals":
            return {
                "data": {
                    "items": [
                        {"proposal_number": "OV-1", "customer_name": "WEG", "customer_code": "0001", "customer_store": "01"},
                    ]
                }
            }
        if path == "/sales-order-otd/panel":
            return {
                "data": {
                    "items": [
                        {
                            "branch": "01",
                            "order_number": "102942",
                            "line_item": "01",
                            "customer_code": "0001",
                            "customer_store": "01",
                        }
                    ]
                }
            }
        return {"data": {"items": []}}

    def list_customer_outbound_invoices(
        self,
        *,
        customer_code,
        customer_store,
        params=None,
    ):
        return {
            "data": {
                "items": [
                    {
                        "invoice_number": "000123",
                        "series": "1",
                        "filial": "01",
                    }
                ]
            }
        }

    def get_outbound_invoice(self, *, branch, invoice_number, invoice_series):
        return {
            "data": {
                "invoice_number": invoice_number,
                "series": invoice_series,
                "filial": branch,
                "customer_code": "0001",
                "customer_store": "01",
            }
        }


def _uc(gateway=None) -> SuggestInteractionMentionsUseCase:
    repo = _Portfolios([_portfolio()])
    return SuggestInteractionMentionsUseCase(
        _Directory(),
        portfolios=repo,
        scope=ResolveCommercialCustomerScopeService(repo),
        gateway=gateway or _OpsGateway(),
    )


def test_suggest_product_via_internal_search() -> None:
    items = _uc().suggest(query="90AAAA", kinds=["product"], actor_user_id="u1")
    assert items[0]["kind"] == "product"
    assert items[0]["ref"]["product_code"] == "90AAAA01"


def test_suggest_product_falls_back_to_factory_status() -> None:
    gateway = _OpsGateway()
    gateway.fail_search = True
    items = _uc(gateway).suggest(query="90AAAA01", kinds=["product"], actor_user_id="u1")
    assert items[0]["ref"]["product_code"] == "90AAAA01"
    assert any(call.endswith("/factory-status") for call in gateway.product_calls)


def test_suggest_production_order_and_opportunity_and_otd() -> None:
    uc = _uc()
    op = uc.suggest(query="00118901001", kinds=["production_order"], actor_user_id="u1")
    assert op[0]["kind"] == "production_order"
    ov = uc.suggest(query="OV", kinds=["opportunity"], actor_user_id="u1")
    assert ov[0]["ref"]["proposal_number"] == "OV-1"
    otd = uc.suggest(query="102942", kinds=["otd_line"], actor_user_id="u1")
    assert otd[0]["ref"] == {"branch": "01", "order": "102942", "line": "01"}


def test_suggest_invoice_from_membership_customers() -> None:
    items = _uc().suggest(query="000123", kinds=["invoice"], actor_user_id="u1")
    assert items[0]["kind"] == "invoice"
    assert items[0]["ref"]["invoice"] == "000123"


def test_suggest_ops_gateway_error_is_empty() -> None:
    class Boom(_OpsGateway):
        def get_product(self, path, *, params=None):
            raise RuntimeError("down")

        def get_production(self, path, *, params=None):
            raise RuntimeError("down")

        def get_commercial_analytics(self, path, *, params=None):
            raise RuntimeError("down")

        def list_customer_outbound_invoices(self, **kwargs):
            raise RuntimeError("down")

    items = _uc(Boom()).suggest(
        query="x",
        kinds=["product", "production_order", "opportunity", "otd_line", "invoice"],
        actor_user_id="u1",
    )
    assert items == []


def test_suggest_opportunity_out_of_membership_is_empty() -> None:
    class OtherCustomer(_OpsGateway):
        def get_commercial_analytics(self, path, *, params=None):
            return {
                "data": {
                    "items": [
                        {
                            "proposal_number": "OV-9",
                            "customer_code": "9999",
                            "customer_store": "01",
                        }
                    ]
                }
            }

    items = _uc(OtherCustomer()).suggest(
        query="OV",
        kinds=["opportunity"],
        actor_user_id="u1",
    )
    assert items == []
