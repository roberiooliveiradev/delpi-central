from app.application.models.page import Page
from app.application.dto.lmp.list_lmp_request import ListLMPRequest
from app.domain.entities.lmp.lmp import LMP
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort


class ListLMPUseCase:

    def __init__(self, repository: LMPQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: ListLMPRequest) -> Page[LMP]:
        return self._repository.list_lmps_page(request)