from abc import ABC, abstractmethod


class VisionLlmGatewayPort(ABC):
    @abstractmethod
    def describe(
        self,
        *,
        prompt: str,
        images_b64: list[str],
        max_tokens: int,
    ) -> str:
        raise NotImplementedError

    def provider_name(self) -> str:
        return "unknown"
