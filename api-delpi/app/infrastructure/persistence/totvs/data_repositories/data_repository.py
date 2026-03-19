# app/infrastructure/persistence/totvs/data_repository.py
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.domain.ports.data.data_repository_port import DataRepositoryPort


class DataRepository(BaseRepository, DataRepositoryPort):

    def execute_raw_sql(self, sql: str):

        with self as repo:
            resultsets = repo.execute_query_multiple(sql)

        return resultsets