from app.application.use_cases.financeiro_despesas_centro_custo.get_despesas_centro_custo_filtros_use_case import (
    GetDespesasCentroCustoFiltrosUseCase,
)
from app.application.use_cases.financeiro_despesas_centro_custo.get_despesas_centro_custo_lancamentos_use_case import (
    GetDespesasCentroCustoLancamentosUseCase,
)
from app.application.use_cases.financeiro_despesas_centro_custo.get_despesas_centro_custo_ranking_centros_use_case import (
    GetDespesasCentroCustoRankingCentrosUseCase,
)
from app.application.use_cases.financeiro_despesas_centro_custo.get_despesas_centro_custo_ranking_fornecedores_use_case import (
    GetDespesasCentroCustoRankingFornecedoresUseCase,
)
from app.application.use_cases.financeiro_despesas_centro_custo.get_despesas_centro_custo_resumo_use_case import (
    GetDespesasCentroCustoResumoUseCase,
)
from app.application.use_cases.financeiro_despesas_centro_custo.get_despesas_centro_custo_serie_use_case import (
    GetDespesasCentroCustoSerieUseCase,
)
from app.infrastructure.persistence.totvs.financeiro_despesas_centro_custo.despesas_centro_custo_repository import (
    DespesasCentroCustoRepository,
)


def _repository() -> DespesasCentroCustoRepository:
    return DespesasCentroCustoRepository()


def build_get_despesas_centro_custo_filtros_use_case() -> (
    GetDespesasCentroCustoFiltrosUseCase
):
    return GetDespesasCentroCustoFiltrosUseCase(
        repository=_repository(),
    )


def build_get_despesas_centro_custo_resumo_use_case() -> (
    GetDespesasCentroCustoResumoUseCase
):
    return GetDespesasCentroCustoResumoUseCase(
        repository=_repository(),
    )


def build_get_despesas_centro_custo_serie_use_case() -> (
    GetDespesasCentroCustoSerieUseCase
):
    return GetDespesasCentroCustoSerieUseCase(
        repository=_repository(),
    )


def build_get_despesas_centro_custo_ranking_centros_use_case() -> (
    GetDespesasCentroCustoRankingCentrosUseCase
):
    return GetDespesasCentroCustoRankingCentrosUseCase(
        repository=_repository(),
    )


def build_get_despesas_centro_custo_ranking_fornecedores_use_case() -> (
    GetDespesasCentroCustoRankingFornecedoresUseCase
):
    return GetDespesasCentroCustoRankingFornecedoresUseCase(
        repository=_repository(),
    )


def build_get_despesas_centro_custo_lancamentos_use_case() -> (
    GetDespesasCentroCustoLancamentosUseCase
):
    return GetDespesasCentroCustoLancamentosUseCase(
        repository=_repository(),
    )
