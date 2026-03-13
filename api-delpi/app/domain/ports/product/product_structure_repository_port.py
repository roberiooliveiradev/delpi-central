# app/domain/ports/product_structure_repository_port.py

from abc import ABC, abstractmethod


class ProductStructureRepositoryPort(ABC):

    @abstractmethod
    def fetch_structure_rows(self, code: str, max_depth: int) -> list[dict]:
        raise NotImplementedError