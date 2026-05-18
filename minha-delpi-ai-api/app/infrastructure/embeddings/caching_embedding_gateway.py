from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.services.embedding_cache import EmbeddingCache
from app.infrastructure.config.settings import Settings


class CachingEmbeddingGateway(EmbeddingGatewayPort):
    def __init__(
        self,
        inner: EmbeddingGatewayPort,
        cache: EmbeddingCache | None = None,
    ):
        self.inner = inner
        self.cache = cache or EmbeddingCache(
            ttl_seconds=Settings.EMBEDDING_CACHE_TTL_SECONDS,
            max_entries=Settings.EMBEDDING_CACHE_MAX_ENTRIES,
        )

    def embed(self, text: str) -> list[float]:
        if not Settings.EMBEDDING_CACHE_ENABLED:
            return self.inner.embed(text)

        cached = self.cache.get(text)

        if cached is not None:
            return cached

        embedding = self.inner.embed(text)
        self.cache.set(text, embedding)

        return embedding
