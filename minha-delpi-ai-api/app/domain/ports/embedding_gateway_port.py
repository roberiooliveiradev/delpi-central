from abc import ABC, abstractmethod


class EmbeddingGatewayPort(ABC):
    @abstractmethod
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError
