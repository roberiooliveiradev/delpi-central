from __future__ import annotations

from typing import Any

from app.application.dto.transformometro.dashboard_evolucao_request import (
    DashboardEvolucaoRequest,
)
from app.application.dto.transformometro.dashboard_evolucao_response import (
    DashboardEvolucaoItem,
    DashboardEvolucaoResponse,
)
from app.domain.ports.transformometro.dashboard_port import TransformometroDashboardPort
from transformometro_client import TransformometroApiClient


def _as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class TransformometroDashboardGateway(TransformometroDashboardPort):
    """Proxy do dashboard live do Transformômetro (série Economia bruta vs Investimento)."""

    def __init__(self, client: TransformometroApiClient | None = None) -> None:
        self._client = client or TransformometroApiClient()

    def get_evolucao(
        self,
        request: DashboardEvolucaoRequest,
        *,
        authorization: str | None,
    ) -> DashboardEvolucaoResponse:
        granularity = (request.granularity or "month").strip().lower() or "month"
        if granularity not in {"day", "month"}:
            raise ValueError("granularity inválida. Valores aceitos: day, month.")

        data = self._client.get_dashboard_evolucao(
            params={
                "view": request.view,
                "filial_id": request.filial_id,
                "setor_id": request.setor_id,
                "competencia_inicio": request.competencia_inicio,
                "competencia_fim": request.competencia_fim,
                "granularity": granularity,
            },
            authorization=authorization,
        )

        items = [
            DashboardEvolucaoItem(
                competencia=str(row.get("competencia") or ""),
                economia_bruta=_as_float(row.get("economia_bruta")),
                investimento_unico_mes=_as_float(row.get("investimento_unico_mes")),
                custo_recorrente_mes=_as_float(row.get("custo_recorrente_mes")),
                custo_recursos_compartilhados_mes=_as_float(
                    row.get("custo_recursos_compartilhados_mes")
                ),
                investimento_total_mes=_as_float(row.get("investimento_total_mes")),
                economia_liquida_mes=_as_float(row.get("economia_liquida_mes")),
                horas_economizadas_mes=_as_float(row.get("horas_economizadas_mes")),
                ganho_capacidade=_optional_float(row.get("ganho_capacidade")),
                economia_reducao_volume=_optional_float(row.get("economia_reducao_volume")),
            )
            for row in data.get("items") or []
            if isinstance(row, dict)
        ]

        resolved_granularity = str(data.get("granularity") or granularity).strip().lower()
        if resolved_granularity not in {"day", "month"}:
            resolved_granularity = granularity

        return DashboardEvolucaoResponse(
            total=int(data.get("total") if data.get("total") is not None else len(items)),
            items=items,
            granularity=resolved_granularity,
        )
