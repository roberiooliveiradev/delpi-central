# app/application/use_cases/system/list_table_columns_use_case.py

from app.application.dto.system_requests import ListTableColumnsRequest
from app.domain.ports.system_repository_port import SystemRepositoryPort


class ListTableColumnsUseCase:

    def __init__(self, repository: SystemRepositoryPort):
        self._repository = repository

    def execute(self, request: ListTableColumnsRequest) -> dict:
        return self._repository.get_columns_table(
            table_name=request.table_name,
            page=request.page,
            page_size=request.limit,
        )