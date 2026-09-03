# app/application/use_cases/system/get_table_use_case.py

from app.application.dto.system.system_requests import GetTableRequest
from app.domain.ports.system.system_repository_port import SystemRepositoryPort


class GetTableUseCase:

    def __init__(self, repository: SystemRepositoryPort):
        self._repository = repository

    def execute(self, request: GetTableRequest) -> dict:
        """Retorna um objeto scalar (contrato get_protheus_table), não lista crua."""
        rows = self._repository.get_table(request.table_name)

        if isinstance(rows, dict):
            return rows

        if isinstance(rows, list):
            for item in rows:
                if isinstance(item, dict):
                    return item

            return {}

        return {}
