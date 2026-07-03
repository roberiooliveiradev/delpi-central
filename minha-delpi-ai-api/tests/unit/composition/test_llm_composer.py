import pytest

from app.composition.llm_composer import make_llm_gateway
from app.infrastructure.llm.context_aware_llm_gateway import ContextAwareLlmGateway
from app.infrastructure.llm.llm_gateway_registry import clear_gateway_cache
from app.infrastructure.llm.ollama_llm_gateway import OllamaLlmGateway
from app.infrastructure.llm.openai_compatible_llm_gateway import OpenAiCompatibleLlmGateway


@pytest.fixture(autouse=True)
def _clear_gateway_cache():
    clear_gateway_cache()
    yield
    clear_gateway_cache()


@pytest.mark.parametrize(
    ("provider", "expected"),
    [
        ("ollama", OllamaLlmGateway),
        ("vllm", OpenAiCompatibleLlmGateway),
        ("openai_compatible", OpenAiCompatibleLlmGateway),
        ("openai", OpenAiCompatibleLlmGateway),
    ],
)
def test_make_llm_gateway_resolves_provider(monkeypatch, provider, expected):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    gateway = make_llm_gateway()
    assert isinstance(gateway, ContextAwareLlmGateway)
    assert isinstance(gateway._delegate(), expected)


def test_make_llm_gateway_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic-native")
    gateway = make_llm_gateway()
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        gateway._delegate()
