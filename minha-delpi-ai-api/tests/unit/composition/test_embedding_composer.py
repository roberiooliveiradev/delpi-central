import pytest

from app.composition.embedding_composer import make_embedding_cache, make_embedding_gateway
from app.infrastructure.embeddings.ollama_embedding_gateway import OllamaEmbeddingGateway
from app.infrastructure.embeddings.openai_compatible_embedding_gateway import (
    OpenAiCompatibleEmbeddingGateway,
)


def test_make_embedding_cache_falls_back_to_memory_without_redis(monkeypatch):
    monkeypatch.setattr(
        "app.composition.embedding_composer.Settings.EMBEDDING_CACHE_BACKEND",
        "redis",
    )
    monkeypatch.setattr(
        "app.composition.embedding_composer.Settings.REDIS_URL",
        "",
    )

    cache = make_embedding_cache()
    assert cache.__class__.__name__ == "EmbeddingCache"


@pytest.mark.parametrize(
    ("provider", "expected"),
    [
        ("ollama", OllamaEmbeddingGateway),
        ("openai_compatible", OpenAiCompatibleEmbeddingGateway),
        ("vllm", OpenAiCompatibleEmbeddingGateway),
    ],
)
def test_make_embedding_gateway_resolves_provider(monkeypatch, provider, expected):
    import app.composition.embedding_composer as composer

    monkeypatch.setenv("EMBEDDING_PROVIDER", provider)
    composer._embedding_gateway = None

    gateway = composer.make_embedding_gateway()
    assert isinstance(gateway.inner, expected)
