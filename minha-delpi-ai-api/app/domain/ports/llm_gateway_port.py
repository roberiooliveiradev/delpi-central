from abc import ABC, abstractmethod
from collections.abc import Iterator


class LlmGatewayPort(ABC):
    @abstractmethod
    def generate(self, messages: list[dict]) -> str:
        raise NotImplementedError

    @abstractmethod
    def stream(self, messages: list[dict]) -> Iterator[str]:
        raise NotImplementedError
