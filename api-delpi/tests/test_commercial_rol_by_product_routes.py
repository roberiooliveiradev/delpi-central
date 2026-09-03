"""Smoke — get_commercial_rol_by_product envelope + meta.operationId."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.domain.entities.commercial.rol_by_product import RolByProductResult
from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"


@patch(f"{_COMMERCIAL}.build_get_commercial_rol_by_product_use_case")
def test_get_commercial_rol_by_product_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = RolByProductResult(
        branch="consolidated",
        start_date="2026-06-01",
        end_date="2026-06-30",
        group_by="product",
        market=None,
        items=(),
        export_destination_countries=(),
        total_rol=0.0,
        total_gross_revenue=0.0,
        items_count=0,
    )
    mock_build.return_value = use_case

    response = router_mod.get_commercial_rol_by_product(
        branch=None,
        start_date="2026-06-01",
        end_date="2026-06-30",
        customer_segment=None,
        customer_codes=None,
        customer_names=None,
        exclude_customer_codes=None,
        exclude_customer_names=None,
        product_codes=None,
        product_groups=None,
        market=None,
        group_by="product",
        limit=500,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_commercial_rol_by_product",
        shape="paged_list",
    )
    assert payload["data"]["summary"]["total_rol"] == 0.0
    assert payload["data"]["group_by"] == "product"
    assert payload["data"]["export_destination_countries"] == []
