from app.application.dto.mini_applicators.list_ferramentas_request import (
    ListMiniApplicatorsFerramentasRequest,
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
