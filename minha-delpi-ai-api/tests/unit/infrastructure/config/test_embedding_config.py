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
