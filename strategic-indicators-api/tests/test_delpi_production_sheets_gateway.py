from __future__ import annotations

from unittest.mock import MagicMock

from si_app.infrastructure.gateways.delpi_production_gateway import DelpiProductionSheetsGateway


def test_production_sheets_gateway_maps_direct_labor_pct() -> None:
    client = MagicMock()
    client.get_direct_labor_cost_pct.return_value = {"direct_labor_cost_pct": 3.5}

    gateway = DelpiProductionSheetsGateway(client)
    pct = gateway.get_direct_labor_cost_pct(
        branch="01",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )

    assert pct == 3.5
    client.get_direct_labor_cost_pct.assert_called_once()
