# app/application/use_cases/system/get_table_relations_use_case.py

from app.application.dto.system_requests import GetTableRelationsRequest
from app.domain.ports.system_repository_port import SystemRepositoryPort


class GetTableRelationsUseCase:

    def __init__(self, repository: SystemRepositoryPort):
        self._repository = repository

    def execute(self, request: GetTableRelationsRequest) -> list[dict]:
        return self._repository.get_table_relations(request.table_name)