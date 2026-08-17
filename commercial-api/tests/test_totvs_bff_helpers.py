"""merge_totvs_params — seller_id não vaza para api-delpi; codes vêm do escopo."""

from __future__ import annotations

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.interface.http.routes.totvs_bff_helpers import (
    merge_totvs_params,
    parse_portfolio_id_csv,
    resolve_analytics_portfolio_scope,
)


def _dummy_request():
    from starlette.requests import Request

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_merge_injects_codes_and_drops_empty():
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("ABC", "01")}),
    )
    params = merge_totvs_params(
        scope,
        {
            "start_date": "2026-01-01",
            "branch": "",
            "seller_id": "should-drop",
            "portfolio_id": "also-drop",
        },
    )
    assert params == {
        "start_date": "2026-01-01",
        "customer_codes": "ABC",
    }


def test_merge_unrestricted_omits_codes():
    scope = CommercialCustomerScope(unrestricted=True, allowed_customers=None)
    params = merge_totvs_params(scope, {"branch": "01"})
    assert params == {"branch": "01"}
    assert "customer_codes" not in params


def test_merge_account_customer_code_bypasses_portfolio_membership():
    scope = CommercialCustomerScope(
        unrestricted=False,
        allowed_customers=frozenset({("OTHER", "01")}),
    )
    params = merge_totvs_params(
        scope,
        {"search": "000001", "account_customer_code": "should-drop-from-base"},
        account_customer_code="000001",
    )
    assert params == {
        "search": "000001",
        "customer_codes": "000001",
    }


def test_resolve_analytics_portfolio_scope_empty_is_global():
    scope = resolve_analytics_portfolio_scope(
        _dummy_request(),
        seller_id=None,
        portfolio_id=None,
    )
    assert scope.unrestricted is True
    assert scope.allowed_customers is None


def test_resolve_analytics_portfolio_scope_with_ids_delegates(monkeypatch):
    called: dict[str, object] = {}

    def fake_resolve(request, *, seller_id=None, portfolio_id=None):
        called["seller_id"] = seller_id
        called["portfolio_id"] = portfolio_id
        return CommercialCustomerScope(
            unrestricted=False,
            allowed_customers=frozenset({("001", "01")}),
        )

    import commercial_app.interface.http.routes.totvs_bff_helpers as helpers

    monkeypatch.setattr(helpers, "resolve_portfolio_scope", fake_resolve)
    scope = helpers.resolve_analytics_portfolio_scope(
        _dummy_request(),
        seller_id="p1,p2",
        portfolio_id=None,
    )
    assert called["seller_id"] == "p1,p2"
    assert scope.allowed_customers == frozenset({("001", "01")})


def test_parse_portfolio_id_csv_dedupes_and_splits():
    assert parse_portfolio_id_csv("a, b", "b,c", None, "") == ["a", "b", "c"]
    assert parse_portfolio_id_csv(None, None) == []
