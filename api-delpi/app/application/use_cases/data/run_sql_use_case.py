# app/application/use_cases/data/run_sql_use_case.py
from app.application.dto.data.run_sql_request import RunSqlRequest
from app.domain.ports.data.data_repository_port import DataRepositoryPort
from app.application.services.sql_validator import SqlValidator


class RunSqlUseCase:

    def __init__(self, repository: DataRepositoryPort):
        self.repository = repository
        self.validator = SqlValidator()

    def execute(self, dto: RunSqlRequest):

        # valida SQL
        self.validator.validate(dto.sql)

        # executa
        resultsets = self.repository.execute_raw_sql(dto.sql)

        return {
            "sql": dto.sql,
            "total_resultsets": len(resultsets),
            "resultsets": resultsets
        }