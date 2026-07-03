"""Cache de gateways LLM por provider normalizado."""

from __future__ import annotations

from app.composition.provider_registry import resolve_llm_gateway_factory
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.infrastructure.config.llm_text_config import (
    normalize_llm_provider,
    resolve_llm_provider_name,
)

_GATEWAYS: dict[str, LlmGatewayPort] = {}


def get_gateway_for_provider(provider: str | None = None) -> LlmGatewayPort:
    normalized = normalize_llm_provider(provider or resolve_llm_provider_name())
    cached = _GATEWAYS.get(normalized)

    if cached is not None:
        return cached

    gateway = resolve_llm_gateway_factory(normalized)()
    _GATEWAYS[normalized] = gateway
    return gateway


def clear_gateway_cache() -> None:
    _GATEWAYS.clear()
