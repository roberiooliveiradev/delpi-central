from __future__ import annotations

from delpi_api_client import DelpiApiClient

from maint_app.config import settings
from maint_app.domain.ports.mini_applicators_totvs_port import MiniApplicatorsTotvsPort
from maint_app.infrastructure.gateways.delpi_mini_applicators_gateway import (
    DelpiMiniAplicatorsGateway,
)

_delpi_client: DelpiApiClient | None = None
_totvs_gateway: DelpiMiniAplicatorsGateway | None = None


def _get_delpi_client() -> DelpiApiClient:
    global _delpi_client
    if _delpi_client is None:
        _delpi_client = DelpiApiClient(
            base_url=settings.DELPI_API_URL,
            timeout=float(settings.DELPI_API_TIMEOUT),
            caller_app=settings.DELPI_API_CALLER_APP,
        )
    return _delpi_client


def build_mini_applicators_totvs_gateway() -> MiniApplicatorsTotvsPort:
    global _totvs_gateway
    if _totvs_gateway is None:
        _totvs_gateway = DelpiMiniAplicatorsGateway(_get_delpi_client())
    return _totvs_gateway
