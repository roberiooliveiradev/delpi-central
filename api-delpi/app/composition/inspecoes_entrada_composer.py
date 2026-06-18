from app.application.use_cases.inspecoes_entrada.get_inspecoes_entrada_historico_detalhe_use_case import (
    GetInspecoesEntradaHistoricoDetalheUseCase,
)
from app.application.use_cases.inspecoes_entrada.get_inspecoes_entrada_resumo_use_case import (
    GetInspecoesEntradaResumoUseCase,
)
from app.application.use_cases.inspecoes_entrada.list_inspecoes_entrada_historico_use_case import (
    ListInspecoesEntradaHistoricoUseCase,
)
from app.application.use_cases.inspecoes_entrada.list_inspecoes_entrada_pendentes_fornecedor_use_case import (
    ListInspecoesEntradaPendentesFornecedorUseCase,
)
from app.application.use_cases.inspecoes_entrada.list_inspecoes_entrada_pendentes_use_case import (
    ListInspecoesEntradaPendentesUseCase,
)
from app.application.use_cases.inspecoes_entrada.list_inspecoes_entrada_rejeitadas_ensaiador_use_case import (
    ListInspecoesEntradaRejeitadasEnsaiadorUseCase,
)
from app.application.use_cases.inspecoes_entrada.list_inspecoes_entrada_rejeitadas_produto_use_case import (
    ListInspecoesEntradaRejeitadasProdutoUseCase,
)
from app.infrastructure.persistence.totvs.inspecoes_entrada.inspecoes_entrada_repository import (
    InspecoesEntradaRepository,
)


def build_get_inspecoes_entrada_resumo_use_case() -> GetInspecoesEntradaResumoUseCase:
    return GetInspecoesEntradaResumoUseCase(
        repository=InspecoesEntradaRepository(),
    )


def build_list_inspecoes_entrada_pendentes_use_case() -> ListInspecoesEntradaPendentesUseCase:
    return ListInspecoesEntradaPendentesUseCase(
        repository=InspecoesEntradaRepository(),
    )


def build_list_inspecoes_entrada_pendentes_fornecedor_use_case() -> (
    ListInspecoesEntradaPendentesFornecedorUseCase
):
    return ListInspecoesEntradaPendentesFornecedorUseCase(
        repository=InspecoesEntradaRepository(),
    )


def build_list_inspecoes_entrada_rejeitadas_ensaiador_use_case() -> (
    ListInspecoesEntradaRejeitadasEnsaiadorUseCase
):
    return ListInspecoesEntradaRejeitadasEnsaiadorUseCase(
        repository=InspecoesEntradaRepository(),
    )


def build_list_inspecoes_entrada_rejeitadas_produto_use_case() -> (
    ListInspecoesEntradaRejeitadasProdutoUseCase
):
    return ListInspecoesEntradaRejeitadasProdutoUseCase(
        repository=InspecoesEntradaRepository(),
    )


def build_list_inspecoes_entrada_historico_use_case() -> ListInspecoesEntradaHistoricoUseCase:
    return ListInspecoesEntradaHistoricoUseCase(
        repository=InspecoesEntradaRepository(),
    )


def build_get_inspecoes_entrada_historico_detalhe_use_case() -> (
    GetInspecoesEntradaHistoricoDetalheUseCase
):
    return GetInspecoesEntradaHistoricoDetalheUseCase(
        repository=InspecoesEntradaRepository(),
    )
