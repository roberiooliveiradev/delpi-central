from app.application.use_cases.retrabalho.get_retrabalho_custo_x_rol_use_case import (
    GetRetrabalhoCustoXRolUseCase,
)
from app.application.use_cases.retrabalho.get_retrabalho_detalhes_use_case import (
    GetRetrabalhoDetalhesUseCase,
)
from app.application.use_cases.retrabalho.get_retrabalho_filtros_use_case import (
    GetRetrabalhoFiltrosUseCase,
)
from app.application.use_cases.retrabalho.get_retrabalho_health_use_case import (
    GetRetrabalhoHealthUseCase,
)
from app.application.use_cases.retrabalho.get_retrabalho_mensal_use_case import (
    GetRetrabalhoMensalUseCase,
)
from app.application.use_cases.retrabalho.get_retrabalho_rankings_use_case import (
    GetRetrabalhoColaboradoresUseCase,
    GetRetrabalhoRecursosUseCase,
)
from app.application.use_cases.retrabalho.get_retrabalho_resumo_use_case import (
    GetRetrabalhoResumoUseCase,
)
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import (
    FinancialRepository,
)
from app.infrastructure.persistence.totvs.retrabalho.retrabalho_repository import (
    RetrabalhoRepository,
)


def _repository() -> RetrabalhoRepository:
    return RetrabalhoRepository()


def build_get_retrabalho_health_use_case() -> GetRetrabalhoHealthUseCase:
    return GetRetrabalhoHealthUseCase(repository=_repository())


def build_get_retrabalho_filtros_use_case() -> GetRetrabalhoFiltrosUseCase:
    return GetRetrabalhoFiltrosUseCase(repository=_repository())


def build_get_retrabalho_resumo_use_case() -> GetRetrabalhoResumoUseCase:
    return GetRetrabalhoResumoUseCase(repository=_repository())


def build_get_retrabalho_custo_x_rol_use_case() -> GetRetrabalhoCustoXRolUseCase:
    return GetRetrabalhoCustoXRolUseCase(
        retrabalho_repository=_repository(),
        financial_repository=FinancialRepository(),
    )


def build_get_retrabalho_mensal_use_case() -> GetRetrabalhoMensalUseCase:
    return GetRetrabalhoMensalUseCase(repository=_repository())


def build_get_retrabalho_recursos_use_case() -> GetRetrabalhoRecursosUseCase:
    return GetRetrabalhoRecursosUseCase(repository=_repository())


def build_get_retrabalho_colaboradores_use_case() -> GetRetrabalhoColaboradoresUseCase:
    return GetRetrabalhoColaboradoresUseCase(repository=_repository())


def build_get_retrabalho_detalhes_use_case() -> GetRetrabalhoDetalhesUseCase:
    return GetRetrabalhoDetalhesUseCase(repository=_repository())
