from app.application.use_cases.inspecoes_processo.get_inspecoes_processo_historico_detalhe_use_case import (
    GetInspecoesProcessoHistoricoDetalheUseCase,
)
from app.application.use_cases.inspecoes_processo.get_inspecoes_processo_resumo_use_case import (
    GetInspecoesProcessoResumoUseCase,
)
from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_auditoria_apontamentos_use_case import (
    ListInspecoesProcessoAuditoriaApontamentosUseCase,
)
from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_historico_use_case import (
    ListInspecoesProcessoHistoricoUseCase,
)
from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_por_ensaiador_use_case import (
    ListInspecoesProcessoPorEnsaiadorUseCase,
)
from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_por_operacao_use_case import (
    ListInspecoesProcessoPorOperacaoUseCase,
)
from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_por_produto_use_case import (
    ListInspecoesProcessoPorProdutoUseCase,
)
from app.application.use_cases.inspecoes_processo.list_inspecoes_processo_ranking_ensaio_use_case import (
    ListInspecoesProcessoRankingEnsaioUseCase,
)
from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_repository import (
    InspecoesProcessoRepository,
)

def build_get_inspecoes_processo_resumo_use_case() -> GetInspecoesProcessoResumoUseCase:
    return GetInspecoesProcessoResumoUseCase(
        repository=InspecoesProcessoRepository(),
    )


def build_list_inspecoes_processo_ranking_ensaio_use_case() -> (
    ListInspecoesProcessoRankingEnsaioUseCase
):
    return ListInspecoesProcessoRankingEnsaioUseCase(
        repository=InspecoesProcessoRepository(),
    )


def build_list_inspecoes_processo_por_produto_use_case() -> (
    ListInspecoesProcessoPorProdutoUseCase
):
    return ListInspecoesProcessoPorProdutoUseCase(
        repository=InspecoesProcessoRepository(),
    )


def build_list_inspecoes_processo_por_operacao_use_case() -> (
    ListInspecoesProcessoPorOperacaoUseCase
):
    return ListInspecoesProcessoPorOperacaoUseCase(
        repository=InspecoesProcessoRepository(),
    )


def build_list_inspecoes_processo_por_ensaiador_use_case() -> (
    ListInspecoesProcessoPorEnsaiadorUseCase
):
    return ListInspecoesProcessoPorEnsaiadorUseCase(
        repository=InspecoesProcessoRepository(),
    )


def build_list_inspecoes_processo_historico_use_case() -> (
    ListInspecoesProcessoHistoricoUseCase
):
    return ListInspecoesProcessoHistoricoUseCase(
        repository=InspecoesProcessoRepository(),
    )


def build_get_inspecoes_processo_historico_detalhe_use_case() -> (
    GetInspecoesProcessoHistoricoDetalheUseCase
):
    return GetInspecoesProcessoHistoricoDetalheUseCase(
        repository=InspecoesProcessoRepository(),
    )


def build_list_inspecoes_processo_auditoria_apontamentos_use_case() -> (
    ListInspecoesProcessoAuditoriaApontamentosUseCase
):
    return ListInspecoesProcessoAuditoriaApontamentosUseCase(
        repository=InspecoesProcessoRepository(),
    )
