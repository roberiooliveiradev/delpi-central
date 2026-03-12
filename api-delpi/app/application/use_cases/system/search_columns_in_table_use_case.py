# app/application/use_cases/system/search_columns_in_table_use_case.py

from app.application.dto.system_requests import SearchColumnsInTableRequest
from app.domain.ports.system_repository_port import SystemRepositoryPort


class SearchColumnsInTableUseCase:

    def __init__(self, repository: SystemRepositoryPort):
        self._repository = repository

    def execute(self, request: SearchColumnsInTableRequest) -> list[dict]:
        return self._repository.search_columns_in_table(
            table_name=request.table_name,
            text=request.text,
        )