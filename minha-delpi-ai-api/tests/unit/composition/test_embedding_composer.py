from app.composition.embedding_composer import make_embedding_cache
from app.domain.services.embedding_cache import EmbeddingCache


def test_make_embedding_cache_falls_back_to_memory_without_redis(monkeypatch):
    monkeypatch.setattr(
        "app.composition.embedding_composer.Settings.EMBEDDING_CACHE_BACKEND",
        "redis",
    )
    monkeypatch.setattr(
        "app.composition.embedding_composer.Settings.REDIS_URL",
        "redis://127.0.0.1:6399/0",
    )

    cache = make_embedding_cache()

    assert isinstance(cache, EmbeddingCache)
