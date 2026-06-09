from app.infrastructure.embeddings.caching_embedding_gateway import CachingEmbeddingGateway


class FakeInner:
    def __init__(self):
        self.calls = 0
        self.batch_calls = 0

    def embed(self, text: str) -> list[float]:
        self.calls += 1
        return [0.1, 0.2]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        self.batch_calls += 1
        return [[0.1, 0.2] for _ in texts]


class FakeCache:
    def __init__(self):
        self.store: dict[str, list[float]] = {}

    def get(self, text: str) -> list[float] | None:
        return self.store.get(text)

    def set(self, text: str, embedding: list[float]) -> None:
        self.store[text] = embedding


def test_caching_gateway_tracks_hits_and_misses(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.embeddings.caching_embedding_gateway.Settings.EMBEDDING_CACHE_ENABLED",
        True,
    )

    inner = FakeInner()
    cache = FakeCache()
    gateway = CachingEmbeddingGateway(inner, cache=cache)

    assert gateway.embed("a") == [0.1, 0.2]
    assert gateway.embed("a") == [0.1, 0.2]
    assert inner.calls == 1
    assert gateway.cache_stats() == {"hits": 1, "misses": 1, "hitRate": 0.5}


def test_embed_many_uses_cache_for_known_texts(monkeypatch):
    monkeypatch.setattr(
        "app.infrastructure.embeddings.caching_embedding_gateway.Settings.EMBEDDING_CACHE_ENABLED",
        True,
    )

    inner = FakeInner()
    cache = FakeCache()
    cache.set("cached", [9.9, 8.8])
    gateway = CachingEmbeddingGateway(inner, cache=cache)

    result = gateway.embed_many(["cached", "new"])

    assert result == [[9.9, 8.8], [0.1, 0.2]]
    assert inner.calls == 0
    assert inner.batch_calls == 1
    assert gateway.cache_stats() == {"hits": 1, "misses": 1, "hitRate": 0.5}
