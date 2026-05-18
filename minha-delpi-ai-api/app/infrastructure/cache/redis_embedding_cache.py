import hashlib
import json

from app.domain.ports.embedding_cache_port import EmbeddingCachePort


class RedisEmbeddingCache(EmbeddingCachePort):
    def __init__(
        self,
        *,
        redis_url: str,
        ttl_seconds: int,
        key_prefix: str = "emb:",
    ):
        import redis

        self.client = redis.from_url(redis_url, decode_responses=True)
        self.ttl_seconds = max(60, ttl_seconds)
        self.key_prefix = key_prefix
        self.client.ping()

    def get(self, text: str) -> list[float] | None:
        raw = self.client.get(self._key(text))

        if not raw:
            return None

        try:
            payload = json.loads(raw)
            return [float(value) for value in payload]
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

    def set(self, text: str, embedding: list[float]) -> None:
        self.client.setex(
            self._key(text),
            self.ttl_seconds,
            json.dumps(list(embedding)),
        )

    def _key(self, text: str) -> str:
        normalized = " ".join(str(text or "").split())[:4000]
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"{self.key_prefix}{digest}"
