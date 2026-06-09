from app.domain.ports.embedding_cache_port import EmbeddingCachePort
from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.infrastructure.config.settings import Settings


class CachingEmbeddingGateway(EmbeddingGatewayPort):
    def __init__(
        self,
        inner: EmbeddingGatewayPort,
        cache: EmbeddingCachePort | None = None,
    ):
        self.inner = inner
        self.cache = cache
        self.hits = 0
        self.misses = 0

    def cache_stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hitRate": round(self.hits / total, 3) if total else None,
        }

    def embed(self, text: str) -> list[float]:
        if not Settings.EMBEDDING_CACHE_ENABLED or self.cache is None:
            return self.inner.embed(text)

        cached = self.cache.get(text)

        if cached is not None:
            self.hits += 1
            return cached

        self.misses += 1
        embedding = self.inner.embed(text)
        self.cache.set(text, embedding)

        return embedding

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if not Settings.EMBEDDING_CACHE_ENABLED or self.cache is None:
            return self.inner.embed_many(texts)

        results: list[list[float] | None] = [None] * len(texts)
        misses: list[tuple[int, str]] = []

        for index, text in enumerate(texts):
            cached = self.cache.get(text)

            if cached is not None:
                self.hits += 1
                results[index] = cached
            else:
                misses.append((index, text))

        if not misses:
            return [embedding for embedding in results if embedding is not None]

        self.misses += len(misses)
        embedded = self.inner.embed_many([text for _, text in misses])

        for (index, text), embedding in zip(misses, embedded, strict=True):
            self.cache.set(text, embedding)
            results[index] = embedding

        return [embedding for embedding in results if embedding is not None]
