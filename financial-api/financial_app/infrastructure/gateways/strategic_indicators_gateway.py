from __future__ import annotations

from typing import Any

from financial_app.config import settings
from financial_app.domain.errors import StrategicIndicatorsGatewayError

from delpi_auth.service_token import internal_service_authorization
from strategic_indicators_client.client import (
    StrategicIndicatorsApiClient,
    StrategicIndicatorsApiError,
)


class StrategicIndicatorsGateway:
    """Leitura do IDD/IGD direto no dono do bounded context.

    O Portal Financeiro não passa pela api-delpi para indicadores: o
    strategic-indicators-api é a fonte de verdade e aceita token S2S nas rotas
    ``/integrations/dashboard-*``.
    """

    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient(
            base_url=settings.STRATEGIC_INDICATORS_API_BASE_URL,
            timeout_seconds=settings.STRATEGIC_INDICATORS_API_TIMEOUT,
        )

    def fetch_department_indicators(
        self,
        *,
        department_id: str,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any]:
        try:
            return self._client.get_dashboard_department_indicators(
                department_id=department_id,
                competence=competence,
                start_date=start_date,
                end_date=end_date,
                branch=branch,
                authorization=internal_service_authorization(),
            )
        except StrategicIndicatorsApiError as exc:
            raise StrategicIndicatorsGatewayError(
                "Não foi possível consultar os indicadores estratégicos."
            ) from exc

    def fetch_departments_indicators(
        self,
        *,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any]:
        try:
            return self._client.list_dashboard_departments_indicators(
                competence=competence,
                start_date=start_date,
                end_date=end_date,
                branch=branch,
                authorization=internal_service_authorization(),
            )
        except StrategicIndicatorsApiError as exc:
            raise StrategicIndicatorsGatewayError(
                "Não foi possível consultar os indicadores estratégicos."
            ) from exc

    def fetch_global_score(
        self,
        *,
        competence: str | None,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict[str, Any]:
        """IGD consolidado — mesmo hero que alimenta o TV Dashboard."""
        try:
            return self._client.get_tv_dashboard_hero(
                competence=competence,
                start_date=start_date,
                end_date=end_date,
                branch=branch,
                authorization=internal_service_authorization(),
            )
        except StrategicIndicatorsApiError as exc:
            raise StrategicIndicatorsGatewayError(
                "Não foi possível consultar o IGD da Delpi."
            ) from exc
