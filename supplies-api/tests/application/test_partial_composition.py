from __future__ import annotations

from unittest.mock import MagicMock

from app.application.services.overview_composition_service import OverviewCompositionService
from app.domain.entities import EffectiveUser
from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.strategic_indicators_gateway import (
    StrategicIndicatorsGatewayError,
)


def _user() -> EffectiveUser:
    return EffectiveUser(
        id="22222222-2222-2222-2222-222222222222",
        email="analyst@delpi.com.br",
        name="Analyst",
        permissions={
            "supplies.analytics.access",
            "supplies.unit.filial-01",
        },
        access_token="token",
    )


def test_partial_one_kpi_down_keeps_others():
    reads = MagicMock()
    reads.get_otd.side_effect = DelpiApiGatewayError("api-delpi timeout")
    reads.get_stock_value.return_value = {"total_stock_value": 10.0}
    reads.get_inventory_turnover.return_value = {"inventory_turnover_times": 1.0}
    reads.get_cpv.return_value = {"cpv_percentage": 20.0}
    reads.get_negotiation_savings.return_value = {"total_savings": 3.0}
    reads.get_safety_stock_summary.return_value = {"below_safety_stock": 1}

    pr = MagicMock()
    pr.count_open_requests.return_value = 4
    si = MagicMock()
    si.metrics_by_kpi.return_value = {}

    result = OverviewCompositionService(
        delpi_reads=reads,
        purchase_requests=pr,
        strategic_indicators=si,
    ).compose(_user(), branch="01", start_date="2026-09-01", end_date="2026-09-08")

    by_id = {kpi["id"]: kpi for kpi in result["kpis"]}
    assert by_id["KPI-OTD"]["status"] == "unavailable"
    assert by_id["KPI-OTD"]["value"] is None
    assert by_id["KPI-STOCK-VALUE"]["status"] == "available"
    assert by_id["KPI-SC-OPEN"]["status"] == "available"
    assert any(item["kpiId"] == "KPI-OTD" for item in result["partialFailures"])
    assert len([k for k in result["kpis"] if k["status"] == "available"]) == 6


def test_partial_si_failure_does_not_drop_kpis():
    reads = MagicMock()
    reads.get_otd.return_value = {"otd_percentage": 90.0}
    reads.get_stock_value.return_value = {"total_stock_value": 1.0}
    reads.get_inventory_turnover.return_value = {"inventory_turnover_times": 1.0}
    reads.get_cpv.return_value = {"cpv_percentage": 10.0}
    reads.get_negotiation_savings.return_value = {"total_savings": 1.0}
    reads.get_safety_stock_summary.return_value = {"below_safety_stock": 0}

    pr = MagicMock()
    pr.count_open_requests.return_value = 0
    si = MagicMock()
    si.metrics_by_kpi.side_effect = StrategicIndicatorsGatewayError("si down")

    result = OverviewCompositionService(
        delpi_reads=reads,
        purchase_requests=pr,
        strategic_indicators=si,
    ).compose(_user(), branch="01")

    assert all(kpi["status"] == "available" for kpi in result["kpis"])
    assert any(item["source"] == "si" for item in result["partialFailures"])
    assert all(kpi["meta"] is None for kpi in result["kpis"])
    assert all(kpi.get("goalValue") is None for kpi in result["kpis"])
    assert all(kpi.get("comparableGoal") is None for kpi in result["kpis"])
    assert all(kpi["iddScore"] is None for kpi in result["kpis"])
