# app/application/use_cases/system/get_table_schema_use_case.py

from app.application.dto.system_requests import GetTableSchemaRequest
from app.domain.ports.system_repository_port import SystemRepositoryPort


class GetTableSchemaUseCase:

    def __init__(self, repository: SystemRepositoryPort):
        self._repository = repository

    def execute(self, request: GetTableSchemaRequest) -> dict:
        table = self._repository.get_table(request.table_name)
        columns = self._repository.get_columns_table(
            table_name=request.table_name,
            page=1,
            page_size=500,
        )["results"]
        indexes = self._repository.get_table_indexes(request.table_name)
        relations = self._repository.get_table_relations(request.table_name)

        return {
            "table": table,
            "columns": columns,
            "indexes": indexes,
            "relations": relations,
        }