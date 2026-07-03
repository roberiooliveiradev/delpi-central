import pytest

from app.application.services.chat_llm_gateway_resolver_service import (
    ChatLlmGatewayResolverService,
)
from app.domain.services.chat_llm_generation_context_service import (
    get_active_llm_provider,
    llm_provider_scope,
)
from app.infrastructure.llm.context_aware_llm_gateway import ContextAwareLlmGateway
from app.infrastructure.llm.llm_gateway_registry import clear_gateway_cache, get_gateway_for_provider
from app.infrastructure.llm.ollama_llm_gateway import OllamaLlmGateway
from app.infrastructure.llm.openai_compatible_llm_gateway import OpenAiCompatibleLlmGateway


@pytest.fixture(autouse=True)
def _clear_gateway_cache():
    clear_gateway_cache()
    yield
    clear_gateway_cache()


def test_resolve_effective_provider_uses_agent_override(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    agent = {"metadata": {"llmProviderOverride": "openai_compatible"}}

    assert (
        ChatLlmGatewayResolverService.resolve_effective_provider(agent)
        == "openai_compatible"
    )


def test_resolve_effective_provider_falls_back_to_env(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")

    assert ChatLlmGatewayResolverService.resolve_effective_provider(None) == "ollama"


def test_context_aware_gateway_delegates_to_active_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    gateway = ContextAwareLlmGateway()

    with llm_provider_scope("openai_compatible"):
        assert isinstance(gateway._delegate(), OpenAiCompatibleLlmGateway)

    assert isinstance(gateway._delegate(), OllamaLlmGateway)


def test_get_active_llm_provider_uses_scope(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")

    with llm_provider_scope("openai_compatible"):
        assert get_active_llm_provider() == "openai_compatible"

    assert get_active_llm_provider() == "ollama"


def test_gateway_registry_caches_instances(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    first = get_gateway_for_provider("ollama")
    second = get_gateway_for_provider("ollama")

    assert first is second
