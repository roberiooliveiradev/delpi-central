# app/application/use_cases/transforma_mais/list_process_use_case.py
from typing import List

from app.application.dto.transforma_mais.process_request import ProcessRequest
from app.application.dto.transforma_mais.raw_data import TransformaMaisRawData
from app.domain.entities.transforma_mais.process import Process
from app.domain.ports.transforma_mais.process_query_port import ProcessQueryRepositoryPort
from app.domain.services.transforma_mais.process_summary_calculator import (
    ProcessSummaryCalculator,
)


class ListProcessUseCase:
    def __init__(
        self,
        repository: ProcessQueryRepositoryPort,
        calculator: ProcessSummaryCalculator,
    ):
        self.repository = repository
        self.calculator = calculator

    def execute(self, request: ProcessRequest) -> List[Process]:
        raw = self.repository.load_raw_data()
        items = self.calculator.build_process_list(raw)
        return self._apply_filters(items, request)

    def _apply_filters(self, items: List[Process], request: ProcessRequest) -> List[Process]:
        result = items

        if request.id:
            result = [item for item in result if request.id.lower() in item.id.lower()]

        if request.name_process:
            result = [
                item for item in result
                if request.name_process.lower() in item.name_process.lower()
            ]

        if request.filial_id:
            result = [
                item for item in result
                if request.filial_id.lower() in (item.filial_id or "").lower()
            ]

        if request.sector_name:
            result = [
                item for item in result
                if request.sector_name.lower() in (item.sector_name or "").lower()
            ]

        if request.status:
            result = [
                item for item in result
                if request.status.lower() in (item.status or "").lower()
            ]

        return result