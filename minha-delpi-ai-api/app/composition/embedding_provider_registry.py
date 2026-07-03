from __future__ import annotations

import logging
from collections.abc import Callable

from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.infrastructure.config.embedding_config import (
    normalize_embedding_provider,
    resolve_embedding_provider_name,
)
from app.infrastructure.embeddings.ollama_embedding_gateway import OllamaEmbeddingGateway
from app.infrastructure.embeddings.openai_compatible_embedding_gateway import (
    OpenAiCompatibleEmbeddingGateway,
)

EmbeddingGatewayFactory = Callable[[], EmbeddingGatewayPort]

_EMBEDDING_GATEWAY_FACTORIES: dict[str, EmbeddingGatewayFactory] = {
    "ollama": OllamaEmbeddingGateway,
    "openai_compatible": OpenAiCompatibleEmbeddingGateway,
}


def resolve_embedding_gateway_factory(
    provider: str | None = None,
) -> EmbeddingGatewayFactory:
    normalized = normalize_embedding_provider(provider or resolve_embedding_provider_name())
    factory = _EMBEDDING_GATEWAY_FACTORIES.get(normalized)

    if factory is None:
        supported = ", ".join(sorted(_EMBEDDING_GATEWAY_FACTORIES))
        raise ValueError(
            f"Unsupported embedding provider: {provider or resolve_embedding_provider_name()} "
            f"(supported: {supported})"
        )

    return factory
