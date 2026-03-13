# app/domain/ports/system_repository_port.py

from abc import ABC, abstractmethod


class SystemRepositoryPort(ABC):

    @abstractmethod
    def get_table(self, table_name: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_columns_table(self, table_name: str, page: int = 1, page_size: int = 50) -> dict:
        raise NotImplementedError

    @abstractmethod
    def search_table_by_description(self, description: str, page: int = 1, page_size: int = 20) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_table_indexes(self, table_name: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def get_table_relations(self, table_name: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def search_columns_in_table(self, table_name: str, text: str) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def search_columns_by_description(self, description: str, page: int = 1, page_size: int = 20) -> dict:
        raise NotImplementedError