# app/application/use_cases/kaizen/get_kaizen_summary_use_case.py
from si_app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from si_app.application.dto.kaizen.kaizen_summary_response import KaizenSummaryResponse
from si_app.domain.ports.kaizen.kaizen_query_port import KaizenQueryRepositoryPort


class GetKaizenSummaryUseCase:
    def __init__(self, repository: KaizenQueryRepositoryPort):
        self.repository = repository

    def execute(self, request: KaizenSummaryRequest) -> KaizenSummaryResponse:
        return self.repository.get_kaizen_summary(request)