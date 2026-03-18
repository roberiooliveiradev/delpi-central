# app/application/use_cases/transforma_mais/get_process_summary_use_case.py
from app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from app.application.dto.transforma_mais.process_summary_response import ProcessSummaryResponse
from app.domain.ports.transforma_mais.process_query_port import ProcessQueryRepositoryPort


class GetProcessSummaryUseCase:
    def __init__(self, repository: ProcessQueryRepositoryPort):
        self.repository = repository

    def execute(self, request: ProcessSummaryRequest) -> ProcessSummaryResponse:
        return self.repository.get_process_summary(request)