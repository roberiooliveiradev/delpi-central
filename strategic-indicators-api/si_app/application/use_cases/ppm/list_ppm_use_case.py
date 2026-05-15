# app/application/use_cases/ppm/list_ppm_use_case.py

from si_app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort


class ListPpmUseCase:

    def __init__(self, repository: PpmQueryRepositoryPort):
        self._repository = repository

    def execute(self, request):
        if request.type not in {"internal", "external"}:
            raise ValueError("type deve ser internal ou external")

        return self._repository.list_items(request)