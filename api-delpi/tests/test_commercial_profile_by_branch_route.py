"""Smoke — get_commercial_profile_by_branch."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"


@patch(f"{_COMMERCIAL}.build_get_commercial_profile_by_branch_use_case")
def test_get_commercial_profile_by_branch_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
        "items": [
            {
                "branch": "01",
                "branch_label": "SC",
                "metric": "otd",
                "metric_label": "OTD",
                "value_pct": 91.0,
            },
            {
                "branch": "01",
                "branch_label": "SC",
                "metric": "conversion",
                "metric_label": "Conversão",
                "value_pct": 25.0,
            },
            {
                "branch": "01",
                "branch_label": "SC",
                "metric": "new_business",
                "metric_label": "Novos negócios",
                "value_pct": 40.0,
            },
            {
                "branch": "01",
                "branch_label": "SC",
                "metric": "rol_attainment",
                "metric_label": "Atingimento ROL",
                "value_pct": 99.8,
            },
            {
                "branch": "02",
                "branch_label": "ES",
                "metric": "otd",
                "metric_label": "OTD",
                "value_pct": 88.0,
            },
            {
                "branch": "02",
                "branch_label": "ES",
                "metric": "conversion",
                "metric_label": "Conversão",
                "value_pct": 30.0,
            },
            {
                "branch": "02",
                "branch_label": "ES",
                "metric": "new_business",
                "metric_label": "Novos negócios",
                "value_pct": 35.0,
            },
            {
                "branch": "02",
                "branch_label": "ES",
                "metric": "rol_attainment",
                "metric_label": "Atingimento ROL",
                "value_pct": 80.0,
            },
        ],
        "summary": {"items_count": 8, "branches_count": 2},
    }
    mock_build.return_value = use_case

    response = router_mod.get_commercial_profile_by_branch(
        branch=None,
        start_date="2026-08-01",
        end_date="2026-08-31",
        customer_segment=None,
        customer_codes=None,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_commercial_profile_by_branch",
        shape="paged_list",
        entity="commercial_profile_by_branch",
    )
    assert payload["data"]["summary"]["branches_count"] == 2
    assert len(payload["data"]["items"]) == 8
    assert {row["branch"] for row in payload["data"]["items"]} == {"01", "02"}
    call_request = use_case.execute.call_args.args[0]
    assert call_request.branch is None
    assert call_request.start_date == "2026-08-01"
