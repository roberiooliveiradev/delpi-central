"""Smoke e unidade — série Transformômetro via api-delpi."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.dto.transformometro.dashboard_evolucao_request import (
    DashboardEvolucaoRequest,
)
from app.application.dto.transformometro.dashboard_evolucao_response import (
    DashboardEvolucaoItem,
    DashboardEvolucaoResponse,
)
from app.infrastructure.gateways.transformometro_dashboard_gateway import (
    TransformometroDashboardGateway,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_ENGINEERING = "app.interface.http.routes.engineering.engineering_router"


def test_transformometro_savings_investment_series_returns_meta() -> None:
    from app.interface.http.routes.engineering.engineering_router import (
        get_transformometro_savings_investment_series_route,
    )

    payload = DashboardEvolucaoResponse(
        total=1,
        granularity="day",
        items=[
            DashboardEvolucaoItem(
                competencia="2026-07-01",
                economia_bruta=100.0,
                investimento_unico_mes=10.0,
                custo_recorrente_mes=5.0,
                custo_recursos_compartilhados_mes=0.0,
                investimento_total_mes=15.0,
                economia_liquida_mes=85.0,
                horas_economizadas_mes=2.0,
            )
        ],
    )

    with patch(
        f"{_ENGINEERING}.build_engineering_get_transformometro_savings_investment_series_use_case"
    ) as mock_build:
        mock_build.return_value = MagicMock(execute=MagicMock(return_value=payload))
        response = get_transformometro_savings_investment_series_route(
            view=None,
            filial_id="01",
            setor_id=None,
            start_date="2026-07-01",
            end_date="2026-07-27",
            granularity="day",
        )

    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="get_transformometro_savings_investment_series",
        shape="scalar",
    )
    assert body["data"]["total"] == 1
    assert body["data"]["granularity"] == "day"
    point = body["data"]["points"][0]
    assert point["periodo"] == "2026-07-01"
    assert point["economia_bruta"] == 100.0
    assert point["investimento"] == 15.0
    assert "competencia" not in point
    assert "investimento_total_mes" not in point
    assert "items" not in body["data"]


def test_transformometro_dashboard_gateway_maps_items() -> None:
    client = MagicMock()
    client.get_dashboard_evolucao.return_value = {
        "total": 1,
        "granularity": "month",
        "items": [
            {
                "competencia": "2026-07",
                "economia_bruta": 200,
                "investimento_unico_mes": 20,
                "custo_recorrente_mes": 0,
                "custo_recursos_compartilhados_mes": 0,
                "investimento_total_mes": 20,
                "economia_liquida_mes": 180,
                "horas_economizadas_mes": 4,
                "ganho_capacidade": 1.5,
            }
        ],
    }
    gateway = TransformometroDashboardGateway(client=client)
    result = gateway.get_evolucao(
        DashboardEvolucaoRequest(
            start_date="2026-07-01",
            end_date="2026-07-31",
            granularity="month",
        ),
        authorization="Bearer x",
    )
    assert result.total == 1
    assert result.granularity == "month"
    assert result.items[0].ganho_capacidade == 1.5
    client.get_dashboard_evolucao.assert_called_once()
    call_params = client.get_dashboard_evolucao.call_args.kwargs["params"]
    assert call_params["competencia_inicio"] == "2026-07-01"
    assert call_params["competencia_fim"] == "2026-07-31"
    assert "start_date" not in call_params


def test_transformometro_dashboard_gateway_omits_dates_for_full_history() -> None:
    """Sem start/end → TM recebe None e devolve o histórico completo (mês)."""
    client = MagicMock()
    client.get_dashboard_evolucao.return_value = {
        "total": 2,
        "granularity": "month",
        "items": [
            {
                "competencia": "2025-01",
                "economia_bruta": 10,
                "investimento_unico_mes": 0,
                "custo_recorrente_mes": 0,
                "custo_recursos_compartilhados_mes": 0,
                "investimento_total_mes": 1,
                "economia_liquida_mes": 9,
                "horas_economizadas_mes": 0,
            },
            {
                "competencia": "2026-07",
                "economia_bruta": 20,
                "investimento_unico_mes": 0,
                "custo_recorrente_mes": 0,
                "custo_recursos_compartilhados_mes": 0,
                "investimento_total_mes": 2,
                "economia_liquida_mes": 18,
                "horas_economizadas_mes": 0,
            },
        ],
    }
    gateway = TransformometroDashboardGateway(client=client)
    result = gateway.get_evolucao(
        DashboardEvolucaoRequest(granularity="month"),
        authorization="Bearer x",
    )
    assert result.total == 2
    call_params = client.get_dashboard_evolucao.call_args.kwargs["params"]
    assert call_params["competencia_inicio"] is None
    assert call_params["competencia_fim"] is None
    assert call_params["granularity"] == "month"


def test_transformometro_dashboard_gateway_blank_dates_become_none() -> None:
    client = MagicMock()
    client.get_dashboard_evolucao.return_value = {"total": 0, "granularity": "month", "items": []}
    gateway = TransformometroDashboardGateway(client=client)
    gateway.get_evolucao(
        DashboardEvolucaoRequest(
            start_date="2025-07-01",
            end_date="  ",
            granularity="month",
        ),
        authorization="Bearer x",
    )
    call_params = client.get_dashboard_evolucao.call_args.kwargs["params"]
    assert call_params["competencia_inicio"] == "2025-07-01"
    assert call_params["competencia_fim"] is None


def test_transformometro_dashboard_gateway_start_only_forwards_partial() -> None:
    client = MagicMock()
    client.get_dashboard_evolucao.return_value = {"total": 0, "granularity": "month", "items": []}
    gateway = TransformometroDashboardGateway(client=client)
    gateway.get_evolucao(
        DashboardEvolucaoRequest(start_date="2025-07-01", granularity="month"),
        authorization="Bearer x",
    )
    call_params = client.get_dashboard_evolucao.call_args.kwargs["params"]
    assert call_params["competencia_inicio"] == "2025-07-01"
    assert call_params["competencia_fim"] is None
