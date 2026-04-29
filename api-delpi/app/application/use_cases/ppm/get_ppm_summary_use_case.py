# app/application/use_cases/ppm/get_ppm_summary_use_case.py

from app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort


class GetPpmSummaryUseCase:

    def __init__(self, repository: PpmQueryRepositoryPort):
        self._repository = repository

    def execute(self, request):
        if request.type not in {"internal", "external"}:
            raise ValueError("type deve ser internal ou external")

        return self._repository.get_summary(request)

    def list_branches(
        self,
        *,
        ppm_type: str,
        date_start: str | None,
        date_end: str | None,
    ) -> list[str]:
        if ppm_type not in {"internal", "external"}:
            raise ValueError("ppm_type deve ser internal ou external")

        if not hasattr(self._repository, "list_branches"):
            return []

        return self._repository.list_branches(
            ppm_type=ppm_type,
            date_start=date_start,
            date_end=date_end,
        )