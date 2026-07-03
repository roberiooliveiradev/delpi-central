import logging

from app.composition.embedding_provider_registry import resolve_embedding_gateway_factory
from app.domain.ports.embedding_cache_port import EmbeddingCachePort
from app.domain.ports.embedding_gateway_port import EmbeddingGatewayPort
from app.domain.services.embedding_cache import EmbeddingCache
from app.infrastructure.cache.redis_embedding_cache import RedisEmbeddingCache
from app.infrastructure.config.settings import Settings
from app.infrastructure.embeddings.caching_embedding_gateway import CachingEmbeddingGateway

logger = logging.getLogger(__name__)

_embedding_gateway: CachingEmbeddingGateway | None = None


def make_embedding_cache() -> EmbeddingCachePort:
    backend = (Settings.EMBEDDING_CACHE_BACKEND or "memory").strip().lower()

    if backend == "redis" and Settings.REDIS_URL:
        try:
            return RedisEmbeddingCache(
                redis_url=Settings.REDIS_URL,
                ttl_seconds=Settings.EMBEDDING_CACHE_TTL_SECONDS,
            )
        except Exception as error:
            logger.warning(
                "embedding cache redis unavailable, using memory: %s",
                error,
            )

    return EmbeddingCache(
        ttl_seconds=Settings.EMBEDDING_CACHE_TTL_SECONDS,
        max_entries=Settings.EMBEDDING_CACHE_MAX_ENTRIES,
    )


def make_raw_embedding_gateway() -> EmbeddingGatewayPort:
    return resolve_embedding_gateway_factory()()


def make_embedding_gateway() -> CachingEmbeddingGateway:
    global _embedding_gateway

    if _embedding_gateway is None:
        _embedding_gateway = CachingEmbeddingGateway(
            make_raw_embedding_gateway(),
            cache=make_embedding_cache(),
        )

    return _embedding_gateway


def get_embedding_cache_stats() -> dict | None:
    gateway = make_embedding_gateway()
    return gateway.cache_stats()
