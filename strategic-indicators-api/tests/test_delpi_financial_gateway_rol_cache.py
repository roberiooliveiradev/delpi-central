from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.services.strategic_indicators import snapshot_shared_cache
from si_app.infrastructure.gateways.delpi_financial_gateway import DelpiFinancialGateway


def test_get_rol_uses_shared_ttl_cache(monkeypatch) -> None:
    snapshot_shared_cache._rol_cache.invalidate_all()
    client = MagicMock()
    client.get_rol.return_value = {"rol": 100.0}
    gateway = DelpiFinancialGateway(client)

    first = gateway.get_rol(
        branch="01",
        start_date="01-05-2026",
        end_date="31-05-2026",
    )
    second = gateway.get_rol(
        branch="01",
        start_date="01-05-2026",
        end_date="31-05-2026",
    )

    assert first == {"rol": 100.0}
    assert second == {"rol": 100.0}
    client.get_rol.assert_called_once()


def test_list_rol_by_branch_reuses_cached_branches(monkeypatch) -> None:
    snapshot_shared_cache._rol_cache.invalidate_all()
    client = MagicMock()
    client.get_rol.side_effect = [
        {"rol": 100.0},
        {"rol": 200.0},
    ]
    gateway = DelpiFinancialGateway(client)

    first = gateway.list_rol_by_branch(
        branches=["01", "02"],
        start_date="01-05-2026",
        end_date="31-05-2026",
    )
    second = gateway.list_rol_by_branch(
        branches=["01", "02"],
        start_date="01-05-2026",
        end_date="31-05-2026",
    )

    assert first == {"01": {"rol": 100.0}, "02": {"rol": 200.0}}
    assert second == first
    assert client.get_rol.call_count == 2
