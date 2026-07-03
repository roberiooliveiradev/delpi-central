from __future__ import annotations

from collections.abc import Callable

from app.domain.ports.vision_llm_gateway_port import VisionLlmGatewayPort
from app.infrastructure.config.vision_llm_config import (
    normalize_vision_llm_provider,
    resolve_vision_llm_provider_name,
)
from app.infrastructure.llm.ollama_vision_llm_gateway import OllamaVisionLlmGateway
from app.infrastructure.llm.openai_compatible_vision_llm_gateway import (
    OpenAiCompatibleVisionLlmGateway,
)

VisionLlmGatewayFactory = Callable[[], VisionLlmGatewayPort]

_VISION_GATEWAY_FACTORIES: dict[str, VisionLlmGatewayFactory] = {
    "ollama": OllamaVisionLlmGateway,
    "openai_compatible": OpenAiCompatibleVisionLlmGateway,
}


def resolve_vision_llm_gateway_factory(
    provider: str | None = None,
) -> VisionLlmGatewayFactory:
    normalized = normalize_vision_llm_provider(provider or resolve_vision_llm_provider_name())

    if normalized == "off":
        raise ValueError("Vision LLM provider is disabled")

    factory = _VISION_GATEWAY_FACTORIES.get(normalized)

    if factory is None:
        supported = ", ".join(sorted(_VISION_GATEWAY_FACTORIES))
        raise ValueError(
            f"Unsupported vision LLM provider: {provider or resolve_vision_llm_provider_name()} "
            f"(supported: {supported})"
        )

    return factory
