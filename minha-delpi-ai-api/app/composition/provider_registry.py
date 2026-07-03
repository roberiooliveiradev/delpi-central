from __future__ import annotations

from collections.abc import Callable

from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.infrastructure.config.llm_text_config import (
    normalize_llm_provider,
    resolve_llm_provider_name,
)
from app.infrastructure.llm.ollama_llm_gateway import OllamaLlmGateway
from app.infrastructure.llm.openai_compatible_llm_gateway import OpenAiCompatibleLlmGateway

LlmGatewayFactory = Callable[[], LlmGatewayPort]

_LLM_GATEWAY_FACTORIES: dict[str, LlmGatewayFactory] = {
    "ollama": OllamaLlmGateway,
    "openai_compatible": OpenAiCompatibleLlmGateway,
}


def resolve_llm_gateway_factory(provider: str | None = None) -> LlmGatewayFactory:
    normalized = normalize_llm_provider(provider or resolve_llm_provider_name())
    factory = _LLM_GATEWAY_FACTORIES.get(normalized)

    if factory is None:
        supported = ", ".join(sorted(_LLM_GATEWAY_FACTORIES))
        raise ValueError(
            f"Unsupported LLM provider: {provider or resolve_llm_provider_name()} "
            f"(supported: {supported})"
        )

    return factory
