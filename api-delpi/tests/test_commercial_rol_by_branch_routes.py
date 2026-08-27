"""Smoke — get_commercial_rol_by_branch envelope + meta.operationId."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"


@patch(f"{_COMMERCIAL}.build_get_commercial_rol_by_branch_use_case")
def test_get_commercial_rol_by_branch_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
        "items": [
            {
                "branch": "01",
                "rol": 100.0,
                "gross_revenue": 120.0,
                "returns": 5.0,
                "discounts": 3.0,
            },
            {
                "branch": "02",
                "rol": 80.0,
                "gross_revenue": 90.0,
                "returns": 2.0,
                "discounts": 1.0,
            },
        ],
        "summary": {"items_count": 2, "total_rol": 180.0},
    }
    mock_build.return_value = use_case

    response = router_mod.get_commercial_rol_by_branch(
        start_date="2026-06-01",
        end_date="2026-06-30",
        customer_segment=None,
        customer_codes=None,
        customer_names=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_commercial_rol_by_branch",
        shape="paged_list",
    )
    assert len(payload["data"]["items"]) == 2
    assert payload["data"]["items"][0]["branch"] == "01"
    assert payload["data"]["summary"]["total_rol"] == 180.0


def test_get_commercial_rol_by_branch_use_case_builds_items():
    from app.application.dto.commercial.get_rol_by_branch_request import (
        GetRolByBranchRequest,
    )
    from app.application.use_cases.commercial.get_commercial_rol_by_branch_use_case import (
        GetCommercialRolByBranchUseCase,
    )

    financial = MagicMock()
    financial.get_rol.side_effect = [
        {"rol": 10, "gross_revenue": 12, "returns": 1, "discounts": 0},
        {"rol": 20, "gross_revenue": 22, "returns": 0, "discounts": 1},
    ]
    result = GetCommercialRolByBranchUseCase(
        financial_query_repository=financial
    ).execute(
        GetRolByBranchRequest(start_date="2026-06-01", end_date="2026-06-30")
    )
    assert [row["branch"] for row in result["items"]] == ["01", "02"]
    assert result["summary"]["total_rol"] == 30.0
