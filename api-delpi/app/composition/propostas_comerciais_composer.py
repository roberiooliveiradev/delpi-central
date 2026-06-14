from app.application.propostas_comerciais.use_cases.get_proposta_comercial_use_case import (
    GetPropostaComercialUseCase,
)
from app.application.propostas_comerciais.use_cases.list_propostas_comerciais_use_case import (
    ListPropostasComerciaisUseCase,
)
from app.infrastructure.totvs.propostas_comerciais.proposta_comercial_repository import (
    PropostaComercialRepository,
)


def build_list_propostas_comerciais_use_case() -> ListPropostasComerciaisUseCase:
    return ListPropostasComerciaisUseCase(repository=PropostaComercialRepository())


def build_get_proposta_comercial_use_case() -> GetPropostaComercialUseCase:
    return GetPropostaComercialUseCase(repository=PropostaComercialRepository())
