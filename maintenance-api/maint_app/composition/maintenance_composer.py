from __future__ import annotations

from delpi_api_client import DelpiApiClient

from maint_app.config import settings
from maint_app.domain.ports.mini_applicators_totvs_port import MiniApplicatorsTotvsPort
from maint_app.domain.ports.machine_programs_totvs_port import MachineProgramsTotvsPort
from maint_app.infrastructure.gateways.delpi_mini_applicators_gateway import (
    DelpiMiniAplicatorsGateway,
)
from maint_app.infrastructure.gateways.delpi_machine_programs_gateway import (
    DelpiMachineProgramsGateway,
)

_delpi_client: DelpiApiClient | None = None
_totvs_gateway: DelpiMiniAplicatorsGateway | None = None
_machine_programs_gateway: DelpiMachineProgramsGateway | None = None


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


def build_machine_programs_totvs_gateway() -> MachineProgramsTotvsPort:
    global _machine_programs_gateway
    if _machine_programs_gateway is None:
        _machine_programs_gateway = DelpiMachineProgramsGateway(_get_delpi_client())
    return _machine_programs_gateway


def build_programas_maquina_service():
    from maint_app.application.services.programas_maquina_service import (
        ProgramasMaquinaService,
    )

    return ProgramasMaquinaService(
        totvs_gateway=build_machine_programs_totvs_gateway(),
    )


def build_reposicao_service():
    from maint_app.application.services.reposicao_service import ReposicaoService

    return ReposicaoService(totvs_gateway=build_mini_applicators_totvs_gateway())


def build_preventiva_service():
    from maint_app.application.services.preventiva_service import PreventivaService

    return PreventivaService(totvs_gateway=build_mini_applicators_totvs_gateway())


def build_revisao_programada_service():
    from maint_app.application.services.revisao_programada_service import RevisaoProgramadaService

    return RevisaoProgramadaService(totvs_gateway=build_mini_applicators_totvs_gateway())
