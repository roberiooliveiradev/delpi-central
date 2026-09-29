from functools import lru_cache

from delpi_mes_app.application.services.mes_read_service import MesReadService
from delpi_mes_app.config import settings
from delpi_mes_app.infrastructure.gateways.production_control_mes_gateway import (
    ProductionControlMesGateway,
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
