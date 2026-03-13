# app/domain/ports/product_parents_repository_port.py
from abc import ABC, abstractmethod


class ProductParentsRepositoryPort(ABC):

    @abstractmethod
    def fetch_parents_rows(self, code: str, max_depth: int) -> list[dict]:
        raise NotImplementedError