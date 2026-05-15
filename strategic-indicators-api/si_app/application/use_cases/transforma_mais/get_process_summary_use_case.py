# app/application/use_cases/transforma_mais/get_process_summary_use_case.py
from si_app.application.dto.transforma_mais.process_summary_request import ProcessSummaryRequest
from si_app.application.dto.transforma_mais.process_summary_response import ProcessSummaryResponse
from si_app.domain.ports.transforma_mais.process_query_port import ProcessQueryRepositoryPort
from si_app.domain.services.transforma_mais.process_summary_calculator import (
    ProcessSummaryCalculator,
)


class GetProcessSummaryUseCase:
    def __init__(
        self,
        repository: ProcessQueryRepositoryPort,
        calculator: ProcessSummaryCalculator,
    ):
        self.repository = repository
        self.calculator = calculator

    def execute(self, request: ProcessSummaryRequest) -> ProcessSummaryResponse:
        raw = self.repository.load_raw_data()

        return self.calculator.build_summary(
            raw=raw,
            filial_id=request.filial_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )