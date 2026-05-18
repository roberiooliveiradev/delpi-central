from app.application.dto.quality.quality_branches_response import QualityBranchesResponse
from app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort


class ListQualityBranchesUseCase:
    def __init__(self, repository: PpmQueryRepositoryPort):
        self._repository = repository

    def execute(
        self,
        *,
        date_start: str | None,
        date_end: str | None,
    ) -> QualityBranchesResponse:
        branches: set[str] = set()

        if hasattr(self._repository, "list_branches"):
            for ppm_type in ("internal", "external"):
                for branch in self._repository.list_branches(
                    ppm_type=ppm_type,
                    date_start=date_start,
                    date_end=date_end,
                ):
                    code = (branch or "").strip()
                    if code:
                        branches.add(code)

        return QualityBranchesResponse(branches=sorted(branches))
