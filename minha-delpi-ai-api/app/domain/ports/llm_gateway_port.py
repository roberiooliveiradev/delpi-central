from abc import ABC, abstractmethod
from collections.abc import Iterator

from app.domain.entities.llm_generation_result import LlmGenerationResult


class LlmGatewayPort(ABC):
    @abstractmethod
    def generate(self, messages: list[dict]) -> str:
        raise NotImplementedError

    @abstractmethod
    def stream(self, messages: list[dict]) -> Iterator[str]:
        raise NotImplementedError

    def supports_native_tools(self) -> bool:
        return False

    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> LlmGenerationResult:
        return LlmGenerationResult(content=self.generate(messages))
