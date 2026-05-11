from abc import ABC, abstractmethod


class LlmGatewayPort(ABC):
    @abstractmethod
    def generate(self, messages: list[dict]) -> str:
        raise NotImplementedError
