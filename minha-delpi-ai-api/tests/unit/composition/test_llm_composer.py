import pytest

from app.composition.llm_composer import make_llm_gateway
from app.infrastructure.llm.ollama_llm_gateway import OllamaLlmGateway
from app.infrastructure.llm.openai_compatible_llm_gateway import OpenAiCompatibleLlmGateway


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
    assert isinstance(gateway, expected)


def test_make_llm_gateway_rejects_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic-native")
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        make_llm_gateway()
