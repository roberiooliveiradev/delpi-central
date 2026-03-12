# app/infrastructure/persistence/totvs/data_repository.py
from app.infrastructure.persistence.base_repository import BaseRepository
from app.domain.ports.data_repository_port import DataRepositoryPort


class DataRepository(BaseRepository, DataRepositoryPort):

    def execute_raw_sql(self, sql: str):

        with self as repo:
            resultsets = repo.execute_query_multiple(sql)

        return resultsets