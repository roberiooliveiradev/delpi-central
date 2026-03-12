# app/domain/ports/data_repository_port.py
from abc import ABC, abstractmethod


class DataRepositoryPort(ABC):

    @abstractmethod
    def execute_raw_sql(self, sql: str) -> dict:
        pass