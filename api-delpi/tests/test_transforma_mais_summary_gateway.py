"""Gateway Transforma Mais — resumo com investimento e soluções do período."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from app.infrastructure.gateways.transformometro_transforma_mais_gateway import (
    TransformometroTransformaMaisGateway,
)


def test_transforma_mais_summary_maps_investment_and_period_kpis() -> None:
    client = MagicMock()
    client.get_engineering_summary.return_value = {
        "implemented_solutions_count": 5,
        "solutions_started_in_period_count": 3,
        "total_net_savings_until_now": 100.0,
        "total_hours_saved_until_now": 12.5,
        "total_gross_costs_until_now": 40.0,
        "total_investment_in_period": 40.0,
        "total_gross_savings_in_period": 200.0,
        "average_roi": 2.5,
        "monthly_breakdown": [],
        "range_summary": {
            "start_date": "2025-02-01",
            "end_date": "2025-02-28",
            "accumulated_net_savings_until_now": 100.0,
        },
    }
    gateway = TransformometroTransformaMaisGateway(client=client)
    result = gateway.get_summary(
        ProcessSummaryRequest(filial_id=None, start_date="2025-02-01", end_date="2025-02-28"),
        authorization="Bearer x",
    )
    payload = result.to_dict()
    assert payload["total_investment_in_period"] == 40.0
    assert payload["total_gross_savings_in_period"] == 200.0
    assert payload["total_hours_saved_until_now"] == 12.5
    assert payload["implemented_solutions_count"] == 5
    assert payload["solutions_started_in_period_count"] == 3


def test_transforma_mais_summary_todas_omits_filial_upstream() -> None:
    """branch=Todas no OpenAPI não deve ir como literal ao Transformômetro."""
    client = MagicMock()
    client.get_engineering_summary.return_value = {
        "implemented_solutions_count": 0,
        "solutions_started_in_period_count": 0,
        "total_net_savings_until_now": 0.0,
        "total_hours_saved_until_now": 0.0,
        "total_gross_costs_until_now": 0.0,
        "total_investment_in_period": 0.0,
        "total_gross_savings_in_period": 0.0,
        "average_roi": 0.0,
        "monthly_breakdown": [],
    }
    gateway = TransformometroTransformaMaisGateway(client=client)
    gateway.get_summary(
        ProcessSummaryRequest(filial_id="Todas", start_date=None, end_date=None),
        authorization=None,
    )
    params = client.get_engineering_summary.call_args.kwargs["params"]
    assert params["filial_id"] is None


def test_transforma_mais_summary_keeps_concrete_filial() -> None:
    client = MagicMock()
    client.get_engineering_summary.return_value = {
        "implemented_solutions_count": 0,
        "solutions_started_in_period_count": 0,
        "total_net_savings_until_now": 0.0,
        "total_hours_saved_until_now": 0.0,
        "total_gross_costs_until_now": 0.0,
        "total_investment_in_period": 0.0,
        "total_gross_savings_in_period": 0.0,
        "average_roi": 0.0,
        "monthly_breakdown": [],
    }
    gateway = TransformometroTransformaMaisGateway(client=client)
    gateway.get_summary(
        ProcessSummaryRequest(filial_id="02", start_date=None, end_date=None),
        authorization=None,
    )
    params = client.get_engineering_summary.call_args.kwargs["params"]
    assert params["filial_id"] == "02"
