"""merge_totvs_params — seller_id não vaza para api-delpi; codes vêm do escopo."""

from __future__ import annotations

from commercial_app.application.services.resolve_commercial_customer_scope_service import (
    CommercialCustomerScope,
)
from commercial_app.interface.http.routes.totvs_bff_helpers import (
    merge_totvs_params,
    parse_portfolio_id_csv,
)


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


def test_parse_portfolio_id_csv_dedupes_and_splits():
    assert parse_portfolio_id_csv("a, b", "b,c", None, "") == ["a", "b", "c"]
    assert parse_portfolio_id_csv(None, None) == []
