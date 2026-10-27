from functools import lru_cache

from delpi_mes_app.application.services.mes_downtime_management_service import (
    MesDowntimeManagementService,
)
from delpi_mes_app.application.services.mes_downtime_reason_admin_service import (
    MesDowntimeReasonAdminService,
)
from delpi_mes_app.application.services.mes_read_service import MesReadService
from delpi_mes_app.config import settings
from delpi_mes_app.infrastructure.gateways.production_control_mes_gateway import (
    ProductionControlMesGateway,
)
from delpi_mes_app.infrastructure.gateways.requests_api_gateway import (
    RequestsApiGateway,
)


@lru_cache(maxsize=1)
def build_gateway() -> ProductionControlMesGateway:
    return ProductionControlMesGateway(
        base_url=settings.PRODUCTION_CONTROL_API_URL,
        timeout=settings.PRODUCTION_CONTROL_API_TIMEOUT,
    )


def close_gateway() -> None:
    if build_gateway.cache_info().currsize:
        build_gateway().close()
        build_gateway.cache_clear()


def build_mes_read_service() -> MesReadService:
    return MesReadService(build_gateway())


def build_mes_downtime_reason_admin_service() -> MesDowntimeReasonAdminService:
    return MesDowntimeReasonAdminService(build_gateway())


@lru_cache(maxsize=1)
def build_requests_gateway() -> RequestsApiGateway:
    return RequestsApiGateway(
        base_url=settings.REQUESTS_API_URL,
        timeout=settings.REQUESTS_API_TIMEOUT,
    )


def build_mes_downtime_management_service() -> MesDowntimeManagementService:
    return MesDowntimeManagementService(
        mes_gateway=build_gateway(),
        requests_gateway=build_requests_gateway(),
    )
