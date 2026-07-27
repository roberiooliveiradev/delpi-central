"""Smoke e unidade — evolução Transformômetro via api-delpi."""

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


def test_transformometro_dashboard_evolucao_returns_meta() -> None:
    from app.interface.http.routes.engineering.engineering_router import (
        get_transformometro_dashboard_evolucao_route,
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
        f"{_ENGINEERING}.build_engineering_get_transformometro_dashboard_evolucao_use_case"
    ) as mock_build:
        mock_build.return_value = MagicMock(execute=MagicMock(return_value=payload))
        response = get_transformometro_dashboard_evolucao_route(
            view=None,
            filial_id="01",
            setor_id=None,
            competencia_inicio="2026-07-01",
            competencia_fim="2026-07-27",
            granularity="day",
        )

    body = body_json(response)
    assert_envelope_meta(
        body,
        operation_id="get_transformometro_dashboard_evolucao",
        shape="paged_list",
    )
    assert body["data"]["total"] == 1
    assert body["data"]["granularity"] == "day"
    assert body["data"]["items"][0]["economia_bruta"] == 100.0


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
            competencia_inicio="2026-07",
            competencia_fim="2026-07",
            granularity="month",
        ),
        authorization="Bearer x",
    )
    assert result.total == 1
    assert result.granularity == "month"
    assert result.items[0].ganho_capacidade == 1.5
    client.get_dashboard_evolucao.assert_called_once()
