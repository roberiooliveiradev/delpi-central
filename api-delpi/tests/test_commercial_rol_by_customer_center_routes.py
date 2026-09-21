"""Smoke — get_commercial_rol_by_customer_center envelope + meta.operationId."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.domain.entities.commercial.rol_by_customer_center import (
    RolByCustomerCenterResult,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"


def _empty_result() -> RolByCustomerCenterResult:
    return RolByCustomerCenterResult(
        branch="consolidated",
        start_date="2026-06-01",
        end_date="2026-06-30",
        group_by="center",
        market=None,
        items=(),
        total_rol=0.0,
        total_gross_revenue=0.0,
        total_qty=0.0,
        items_count=0,
        unclassified_rol=0.0,
        unclassified_qty=0.0,
    )


@patch(f"{_COMMERCIAL}.build_get_commercial_rol_by_customer_center_use_case")
def test_get_commercial_rol_by_customer_center_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = _empty_result()
    mock_build.return_value = use_case

    response = router_mod.get_commercial_rol_by_customer_center(
        branch=None,
        start_date="2026-06-01",
        end_date="2026-06-30",
        customer_segment=None,
        customer_codes=None,
        customer_stores=None,
        customer_names=None,
        customer_centers=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
        product_codes=None,
        product_groups=None,
        market=None,
        group_by="center",
        limit=500,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_commercial_rol_by_customer_center",
        shape="paged_list",
    )
    assert payload["data"]["summary"]["total_rol"] == 0.0
    assert payload["data"]["summary"]["unclassified_rol"] == 0.0
    assert payload["data"]["group_by"] == "center"
    assert payload["data"]["items"] == []


@patch(f"{_COMMERCIAL}.build_get_commercial_rol_by_customer_center_use_case")
def test_get_commercial_rol_by_customer_center_validation_error(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.side_effect = ValueError("start_date e end_date são obrigatórios.")
    mock_build.return_value = use_case

    response = router_mod.get_commercial_rol_by_customer_center(
        branch=None,
        start_date=None,
        end_date=None,
        customer_segment=None,
        customer_codes=None,
        customer_stores=None,
        customer_names=None,
        customer_centers=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
        product_codes=None,
        product_groups=None,
        market=None,
        group_by="center",
        limit=500,
    )
    payload = body_json(response)
    assert payload["success"] is False
    assert response.status_code == 400
