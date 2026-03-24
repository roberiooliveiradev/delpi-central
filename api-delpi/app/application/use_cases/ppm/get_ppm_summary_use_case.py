# app/application/use_cases/ppm/get_ppm_summary_use_case.py

from app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort


class GetPpmSummaryUseCase:

    def __init__(self, repository: PpmQueryRepositoryPort):
        self._repository = repository

    def execute(self, request):
        if request.type not in {"internal", "external"}:
            raise ValueError("type deve ser internal ou external")

        return self._repository.get_summary(request)