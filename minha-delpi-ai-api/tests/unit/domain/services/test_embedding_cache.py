import time

from app.domain.services.embedding_cache import EmbeddingCache


def test_embedding_cache_returns_cached_value_within_ttl():
    cache = EmbeddingCache(ttl_seconds=60, max_entries=10)

    cache.set("texto", [0.1, 0.2, 0.3])

    assert cache.get("texto") == [0.1, 0.2, 0.3]


def test_embedding_cache_expires_entries():
    cache = EmbeddingCache(ttl_seconds=1, max_entries=10)

    cache.set("texto", [1.0])

    time.sleep(1.1)

    assert cache.get("texto") is None
