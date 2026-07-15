from app.application.use_cases.financeiro_inadimplencia.get_clientes_use_case import (
    GetInadimplenciaClientesUseCase,
)
from app.application.use_cases.financeiro_inadimplencia.get_faixas_atraso_use_case import (
    GetInadimplenciaFaixasAtrasoUseCase,
)
from app.application.use_cases.financeiro_inadimplencia.get_mensal_use_case import (
    GetInadimplenciaMensalUseCase,
)
from app.application.use_cases.financeiro_inadimplencia.get_resumo_use_case import (
    GetInadimplenciaResumoUseCase,
)
from app.application.use_cases.financeiro_inadimplencia.get_titulos_use_case import (
    GetInadimplenciaTitulosUseCase,
)
from app.infrastructure.persistence.totvs.financeiro_inadimplencia.inadimplencia_repository import (
    InadimplenciaRepository,
)


def _repository() -> InadimplenciaRepository:
    return InadimplenciaRepository()


def build_get_inadimplencia_resumo_use_case() -> GetInadimplenciaResumoUseCase:
    return GetInadimplenciaResumoUseCase(repository=_repository())


def build_get_inadimplencia_mensal_use_case() -> GetInadimplenciaMensalUseCase:
    return GetInadimplenciaMensalUseCase(repository=_repository())


def build_get_inadimplencia_faixas_atraso_use_case() -> (
    GetInadimplenciaFaixasAtrasoUseCase
):
    return GetInadimplenciaFaixasAtrasoUseCase(repository=_repository())


def build_get_inadimplencia_clientes_use_case() -> GetInadimplenciaClientesUseCase:
    return GetInadimplenciaClientesUseCase(repository=_repository())


def build_get_inadimplencia_titulos_use_case() -> GetInadimplenciaTitulosUseCase:
    return GetInadimplenciaTitulosUseCase(repository=_repository())
