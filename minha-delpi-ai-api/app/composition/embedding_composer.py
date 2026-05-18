import logging

from app.domain.ports.embedding_cache_port import EmbeddingCachePort
from app.domain.services.embedding_cache import EmbeddingCache
from app.infrastructure.cache.redis_embedding_cache import RedisEmbeddingCache
from app.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


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
