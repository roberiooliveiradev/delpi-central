"""Smoke — get_commercial_rol_summary."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"


@patch(f"{_COMMERCIAL}.enrich_dashboard_metric", side_effect=lambda payload, **_: {
    **payload,
    "comparable_goal": 1000000.0,
    "rol_target_pct": 15.0,
    "target": 1000000.0,
})
@patch(f"{_COMMERCIAL}.build_get_commercial_rol_summary_use_case")
def test_get_commercial_rol_summary_returns_meta(mock_build, _mock_enrich) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "01",
        "start_date": "2026-08-01",
        "end_date": "2026-08-28",
        "rol": 150000.0,
        "gross_revenue": 160000.0,
        "returns": 5000.0,
        "discounts": 5000.0,
    }
    mock_build.return_value = use_case

    response = router_mod.get_commercial_rol_summary(
        branch="01",
        start_date="2026-08-01",
        end_date="2026-08-28",
        customer_segment=None,
        customer_codes=None,
        customer_names=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_commercial_rol_summary",
        shape="scalar",
        entity="commercial_rol_summary",
    )
    assert payload["data"]["rol"] == 150000.0
    assert payload["data"]["comparable_goal"] == 1000000.0
    assert payload["data"]["rol_target_pct"] == 15.0
