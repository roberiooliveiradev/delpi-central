from app.infrastructure.config.embedding_config import (
    normalize_embedding_provider,
    resolve_embedding_config,
)


def test_normalize_embedding_provider_maps_openai_aliases():
    for alias in ("vllm", "openai_compatible", "openai"):
        assert normalize_embedding_provider(alias) == "openai_compatible"


def test_resolve_embedding_config_uses_ollama_defaults(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
    monkeypatch.delenv("EMBEDDING_BASE_URL", raising=False)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test:11434")
    monkeypatch.setenv("EMBEDDING_MODEL", "bge-m3")

    config = resolve_embedding_config()

    assert config.provider == "ollama"
    assert config.base_url == "http://ollama.test:11434"
    assert config.model == "bge-m3"


def test_embedding_provider_inherits_central_llm_and_skips_local_model(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
    monkeypatch.setenv("EMBEDDING_MODEL", "bge-m3")
    monkeypatch.setenv("KIMI_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("KIMI_API_KEY", "sk-test")

    config = resolve_embedding_config()

    assert config.provider == "off"


def test_openai_compatible_embedding_inherits_kimi_credentials(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai_compatible")
    monkeypatch.setenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
    monkeypatch.delenv("EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_TEXT_BASE_URL", raising=False)
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("LLM_TEXT_API_KEY", raising=False)
    monkeypatch.setenv("KIMI_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("KIMI_API_KEY", "sk-or-test")

    config = resolve_embedding_config()

    assert config.provider == "openai_compatible"
    assert config.base_url == "https://openrouter.ai/api/v1"
    assert config.api_key == "sk-or-test"
    assert config.model == "openai/text-embedding-3-small"
