"""Smoke — get_commercial_billing_by_customer_month envelope + meta.operationId."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.domain.entities.commercial.billing_by_customer_month import (
    BillingByCustomerMonthItem,
    BillingByCustomerMonthResult,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"


@patch(f"{_COMMERCIAL}.build_get_billing_by_customer_month_use_case")
def test_get_commercial_billing_by_customer_month_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = BillingByCustomerMonthResult(
        branch="consolidated",
        start_date="2026-01-01",
        end_date="2026-03-31",
        nature="gross",
        months=("2026-01", "2026-02", "2026-03"),
        items=(
            BillingByCustomerMonthItem(
                customer_code="000001",
                customer_store="01",
                customer_name="ACME",
                monthly_values={"2026-01": 100.0, "2026-02": 50.0, "2026-03": 0.0},
                total=150.0,
            ),
        ),
        grand_total=150.0,
        monthly_totals={"2026-01": 100.0, "2026-02": 50.0, "2026-03": 0.0},
        customers_count=1,
        truncated=False,
    )
    mock_build.return_value = use_case

    response = router_mod.get_commercial_billing_by_customer_month(
        branch=None,
        start_date="2026-01-01",
        end_date="2026-03-31",
        customer_segment=None,
        nature="gross",
        limit=5000,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_commercial_billing_by_customer_month",
        shape="paged_list",
    )
    assert payload["data"]["summary"]["grand_total"] == 150.0
    assert payload["data"]["items"][0]["customer_store"] == "01"
    assert payload["data"]["billingNature"] == "gross"
    assert payload["data"]["months"] == ["2026-01", "2026-02", "2026-03"]


@patch(f"{_COMMERCIAL}.build_get_billing_by_customer_month_use_case")
def test_get_commercial_billing_by_customer_month_validation_error(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.side_effect = ValueError("start_date e end_date são obrigatórios.")
    mock_build.return_value = use_case

    response = router_mod.get_commercial_billing_by_customer_month(
        branch=None,
        start_date=None,
        end_date=None,
        customer_segment=None,
        nature="gross",
        limit=5000,
    )
    payload = body_json(response)
    assert payload["success"] is False
    assert response.status_code == 400
