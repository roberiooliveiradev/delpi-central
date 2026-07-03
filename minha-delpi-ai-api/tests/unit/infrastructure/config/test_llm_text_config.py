from app.infrastructure.config.llm_text_config import (
    is_openai_compatible_provider,
    normalize_llm_provider,
    resolve_llm_text_config,
)


def test_normalize_llm_provider_maps_openai_aliases(monkeypatch):
    for alias in ("vllm", "openai_compatible", "openai"):
        assert normalize_llm_provider(alias) == "openai_compatible"


def test_normalize_llm_provider_keeps_ollama():
    assert normalize_llm_provider("ollama") == "ollama"


def test_is_openai_compatible_provider():
    assert is_openai_compatible_provider("vllm") is True
    assert is_openai_compatible_provider("ollama") is False


def test_resolve_llm_text_config_uses_vllm_fallback(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "vllm")
    monkeypatch.delenv("LLM_TEXT_BASE_URL", raising=False)
    monkeypatch.setenv("VLLM_BASE_URL", "https://api.example.com/v1")
    monkeypatch.delenv("LLM_TEXT_MODEL", raising=False)
    monkeypatch.setenv("VLLM_MODEL", "gpt-test")
    monkeypatch.setenv("VLLM_API_KEY", "secret")

    config = resolve_llm_text_config()

    assert config.provider == "openai_compatible"
    assert config.base_url == "https://api.example.com/v1"
    assert config.model == "gpt-test"
    assert config.api_key == "secret"


def test_resolve_llm_text_config_prefers_llm_text_overrides(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_TEXT_BASE_URL", "https://override.example/v1")
    monkeypatch.setenv("LLM_TEXT_MODEL", "override-model")
    monkeypatch.setenv("LLM_TEXT_API_KEY", "override-key")
    monkeypatch.setenv("LLM_TEXT_TIMEOUT_SECONDS", "90")

    config = resolve_llm_text_config()

    assert config.base_url == "https://override.example/v1"
    assert config.model == "override-model"
    assert config.api_key == "override-key"
    assert config.timeout_seconds == 90.0
