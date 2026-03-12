# app/application/use_cases/system/get_table_indexes_use_case.py

from app.application.dto.system_requests import GetTableIndexesRequest
from app.domain.ports.system_repository_port import SystemRepositoryPort


class GetTableIndexesUseCase:

    def __init__(self, repository: SystemRepositoryPort):
        self._repository = repository

    def execute(self, request: GetTableIndexesRequest) -> list[dict]:
        return self._repository.get_table_indexes(request.table_name)