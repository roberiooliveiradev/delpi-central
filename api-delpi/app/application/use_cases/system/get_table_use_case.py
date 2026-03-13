# app/application/use_cases/system/get_table_use_case.py

from app.application.dto.system.system_requests import GetTableRequest
from app.domain.ports.system.system_repository_port import SystemRepositoryPort


class GetTableUseCase:

    def __init__(self, repository: SystemRepositoryPort):
        self._repository = repository

    def execute(self, request: GetTableRequest) -> list[dict]:
        return self._repository.get_table(request.table_name)