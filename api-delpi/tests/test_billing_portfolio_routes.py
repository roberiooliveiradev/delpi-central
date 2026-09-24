"""Smoke Nível A — billing-portfolio family (4 routes)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"


@patch(f"{_COMMERCIAL}.build_get_billing_portfolio_summary_use_case")
def test_get_billing_portfolio_summary_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "02",
        "start_date": "2026-08-10",
        "end_date": "2026-08-16",
        "forecast_value": 66571.05,
        "realized_value": 60000.0,
        "variance_value": -6571.05,
        "nature": "order_gross",
        "quantity_basis": "planned",
        "forecast_date_basis": "C6_ENTREG",
        "realized_date_basis": "D2_EMISSAO",
        "as_of": "live",
        "by_branch": [
            {
                "branch": "02",
                "forecast_value": 66571.05,
                "realized_value": 60000.0,
                "variance_value": -6571.05,
            }
        ],
    }
    mock_build.return_value = use_case

    response = router_mod.get_billing_portfolio_summary(
        branch="02",
        start_date="2026-08-10",
        end_date="2026-08-16",
        customer_segment="new_business",
        customer_codes=None,
        customer_names=None,
        customer_centers=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
        nature="order_gross",
        quantity_basis="planned",
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_billing_portfolio_summary",
        shape="scalar",
        entity="billing_portfolio_summary",
    )
    assert payload["data"]["forecast_value"] == 66571.05
    assert payload["data"]["realized_value"] == 60000.0
    assert payload["data"]["variance_value"] == -6571.05


@patch(f"{_COMMERCIAL}.build_get_billing_portfolio_series_use_case")
def test_get_billing_portfolio_series_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": None,
        "start_date": "2026-08-10",
        "end_date": "2026-08-16",
        "granularity": "week",
        "truncated": False,
        "nature": "order_gross",
        "quantity_basis": "planned",
        "forecast_date_basis": "C6_ENTREG",
        "realized_date_basis": "D2_EMISSAO",
        "as_of": "live",
        "points": [
            {
                "periodo": "10/08/26 – 16/08/26",
                "sort_key": "2026-W33",
                "start_date": "2026-08-10",
                "end_date": "2026-08-16",
                "forecast_value": 100.0,
                "realized_value": 80.0,
                "variance_value": -20.0,
            }
        ],
    }
    mock_build.return_value = use_case

    response = router_mod.get_billing_portfolio_series(
        granularity="week",
        branch=None,
        start_date="2026-08-10",
        end_date="2026-08-16",
        customer_segment=None,
        customer_codes=None,
        customer_names=None,
        customer_centers=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
        nature="order_gross",
        quantity_basis="planned",
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_billing_portfolio_series",
        shape="scalar",
        entity="billing_portfolio_series",
    )
    assert len(payload["data"]["points"]) == 1


@patch(f"{_COMMERCIAL}.build_get_billing_portfolio_by_customer_use_case")
def test_get_billing_portfolio_by_customer_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "02",
        "start_date": "2026-08-10",
        "end_date": "2026-08-16",
        "nature": "order_gross",
        "quantity_basis": "planned",
        "forecast_date_basis": "C6_ENTREG",
        "realized_date_basis": "D2_EMISSAO",
        "as_of": "live",
        "items": [
            {
                "customer_code": "000223",
                "customer_name": "Wanke",
                "branch": "02",
                "forecast_value": 66571.05,
                "realized_value": 55000.0,
                "variance_value": -11571.05,
            }
        ],
        "pagination": {"page": 1, "page_size": 50, "total": 1, "has_more": False},
        "summary": {
            "items_count": 1,
            "customers_count": 1,
            "forecast_value": 66571.05,
            "realized_value": 55000.0,
            "variance_value": -11571.05,
        },
    }
    mock_build.return_value = use_case

    response = router_mod.get_billing_portfolio_by_customer(
        branch="02",
        start_date="2026-08-10",
        end_date="2026-08-16",
        customer_segment=None,
        customer_codes=None,
        customer_names=None,
        customer_centers=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
        nature="order_gross",
        quantity_basis="planned",
        page=1,
        page_size=50,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_billing_portfolio_by_customer",
        shape="paged_list",
        entity="billing_portfolio_by_customer",
    )
    assert payload["data"]["items"][0]["customer_code"] == "000223"


@patch(f"{_COMMERCIAL}.build_get_billing_portfolio_by_branch_use_case")
def test_get_billing_portfolio_by_branch_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
        "nature": "order_gross",
        "quantity_basis": "planned",
        "forecast_date_basis": "C6_ENTREG",
        "realized_date_basis": "D2_EMISSAO",
        "as_of": "live",
        "items": [
            {
                "branch": "01",
                "forecast_value": 100.0,
                "realized_value": 90.0,
                "variance_value": -10.0,
            },
            {
                "branch": "02",
                "forecast_value": 50.0,
                "realized_value": 45.0,
                "variance_value": -5.0,
            },
        ],
        "summary": {
            "items_count": 2,
            "forecast_value": 150.0,
            "realized_value": 135.0,
            "variance_value": -15.0,
        },
    }
    mock_build.return_value = use_case

    response = router_mod.get_billing_portfolio_by_branch(
        branch=None,
        start_date="2026-08-01",
        end_date="2026-08-31",
        customer_segment=None,
        customer_codes=None,
        customer_names=None,
        customer_centers=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
        nature="order_gross",
        quantity_basis="planned",
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_billing_portfolio_by_branch",
        shape="paged_list",
        entity="billing_portfolio_by_branch",
    )
    assert len(payload["data"]["items"]) == 2
