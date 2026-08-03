"""Smoke — get_commercial_rol_by_customer envelope + meta.operationId."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.domain.entities.commercial.rol_by_customer import RolByCustomerResult
from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_COMMERCIAL = "app.interface.http.routes.commercial.commercial_router"


@patch(f"{_COMMERCIAL}.build_get_commercial_rol_by_customer_use_case")
def test_get_commercial_rol_by_customer_returns_meta(mock_build) -> None:
    import app.interface.http.routes.commercial.commercial_router as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = RolByCustomerResult(
        branch="consolidated",
        start_date="2026-06-01",
        end_date="2026-06-30",
        items=(),
        others=None,
        total_rol=0.0,
        customers_count=0,
    )
    mock_build.return_value = use_case

    response = router_mod.get_commercial_rol_by_customer(
        branch=None,
        start_date="2026-06-01",
        end_date="2026-06-30",
        customer_segment=None,
        limit=20,
        include_others=True,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_commercial_rol_by_customer",
        shape="paged_list",
    )
    assert payload["data"]["summary"]["total_rol"] == 0.0
