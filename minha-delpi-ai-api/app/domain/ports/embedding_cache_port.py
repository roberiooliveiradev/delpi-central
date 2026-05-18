from abc import ABC, abstractmethod


class EmbeddingCachePort(ABC):
    @abstractmethod
    def get(self, text: str) -> list[float] | None:
        raise NotImplementedError

    @abstractmethod
    def set(self, text: str, embedding: list[float]) -> None:
        raise NotImplementedError
