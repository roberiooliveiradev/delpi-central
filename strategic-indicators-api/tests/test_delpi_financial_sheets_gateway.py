from __future__ import annotations

from unittest.mock import MagicMock

from si_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialSheetsGateway


def test_financial_sheets_gateway_caches_ebitda_request() -> None:
    client = MagicMock()
    client.get_ebitda_pct.return_value = {"ebitda_over_rol_pct": 12.5}

    gateway = DelpiFinancialSheetsGateway(client)

    gateway.get_ebitda_pct(
        branch="01",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )
    gateway.get_ebitda_pct(
        branch="01",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )

    client.get_ebitda_pct.assert_called_once()
