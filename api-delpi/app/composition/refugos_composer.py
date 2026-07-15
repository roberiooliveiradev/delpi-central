from app.application.use_cases.refugos.get_refugos_filtros_use_case import (
    GetRefugosFiltrosUseCase,
)
from app.application.use_cases.refugos.get_refugos_health_use_case import (
    GetRefugosHealthUseCase,
)
from app.application.use_cases.refugos.get_refugos_rankings_use_case import (
    GetRefugosRankingsUseCase,
)
from app.application.use_cases.refugos.get_refugos_registros_use_case import (
    GetRefugosRegistrosUseCase,
)
from app.application.use_cases.refugos.get_refugos_resumo_use_case import (
    GetRefugosResumoUseCase,
)
from app.infrastructure.persistence.totvs.refugos.refugos_repository import (
    RefugosRepository,
)


def _repository() -> RefugosRepository:
    return RefugosRepository()


def build_get_refugos_health_use_case() -> GetRefugosHealthUseCase:
    return GetRefugosHealthUseCase(repository=_repository())


def build_get_refugos_filtros_use_case() -> GetRefugosFiltrosUseCase:
    return GetRefugosFiltrosUseCase(repository=_repository())


def build_get_refugos_resumo_use_case() -> GetRefugosResumoUseCase:
    return GetRefugosResumoUseCase(repository=_repository())


def build_get_refugos_rankings_use_case() -> GetRefugosRankingsUseCase:
    return GetRefugosRankingsUseCase(repository=_repository())


def build_get_refugos_registros_use_case() -> GetRefugosRegistrosUseCase:
    return GetRefugosRegistrosUseCase(repository=_repository())
