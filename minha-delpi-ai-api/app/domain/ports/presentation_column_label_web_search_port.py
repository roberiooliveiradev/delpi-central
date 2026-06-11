from __future__ import annotations

from abc import ABC, abstractmethod


class PresentationColumnLabelWebSearchPort(ABC):
    """Busca web para contexto de humanização de nomes de campo (somente metadados)."""

    @abstractmethod
    def search(self, query: str, *, max_results: int = 2) -> dict | None:
        raise NotImplementedError
