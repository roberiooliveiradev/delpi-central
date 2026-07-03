from app.application.dto.mini_applicators.list_ferramentas_request import (
    ListMiniApplicatorsFerramentasRequest,
)
from app.application.dto.mini_applicators.list_pecas_reposicao_request import (
    ListMiniApplicatorsPecasReposicaoRequest,
)
from app.application.models.page import Page
from app.domain.entities.mini_applicators.mini_applicator_tool import MiniApplicatorTool
from app.domain.ports.mini_applicators.mini_applicators_repository_port import (
    MiniApplicatorsRepositoryPort,
)


class ListMiniApplicatorsFerramentasUseCase:
    def __init__(self, repository: MiniApplicatorsRepositoryPort):
        self._repository = repository

    def execute(self, request: ListMiniApplicatorsFerramentasRequest) -> Page[MiniApplicatorTool]:
        return self._repository.list_ferramentas(request)


class GetMiniApplicatorsFerramentaUseCase:
    def __init__(self, repository: MiniApplicatorsRepositoryPort):
        self._repository = repository

    def execute(self, codigo: str) -> MiniApplicatorTool | None:
        return self._repository.get_ferramenta(codigo)


class ListMiniApplicatorsPecasUseCase:
    def __init__(self, repository: MiniApplicatorsRepositoryPort):
        self._repository = repository

    def execute(self, codigo_ferramenta: str) -> list[dict]:
        return self._repository.list_pecas(codigo_ferramenta)


class GetMiniApplicatorsGolpesUseCase:
    def __init__(self, repository: MiniApplicatorsRepositoryPort):
        self._repository = repository

    def execute(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        data_inicial: str,
        data_final: str,
    ) -> dict:
        return self._repository.get_golpes(
            filial=filial,
            codigo_ferramenta=codigo_ferramenta,
            data_inicial=data_inicial,
            data_final=data_final,
        )


class ListMiniApplicatorsComponentesUseCase:
    def __init__(self, repository: MiniApplicatorsRepositoryPort):
        self._repository = repository

    def execute(self, *, codigo_ferramenta: str, filial: str) -> list[dict]:
        return self._repository.list_componentes(
            codigo_ferramenta=codigo_ferramenta,
            filial=filial,
        )


class ListMiniApplicatorsPecasReposicaoUseCase:
    def __init__(self, repository: MiniApplicatorsRepositoryPort):
        self._repository = repository

    def execute(self, request: ListMiniApplicatorsPecasReposicaoRequest) -> Page[dict]:
        return self._repository.list_pecas_reposicao(request)
