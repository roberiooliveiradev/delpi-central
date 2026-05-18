import hashlib
import time
from threading import Lock

from app.domain.ports.embedding_cache_port import EmbeddingCachePort


class EmbeddingCache(EmbeddingCachePort):
    def __init__(self, *, ttl_seconds: int, max_entries: int):
        self.ttl_seconds = max(60, ttl_seconds)
        self.max_entries = max(50, max_entries)
        self._store: dict[str, tuple[float, list[float]]] = {}
        self._lock = Lock()

    def get(self, text: str) -> list[float] | None:
        key = self._key(text)
        now = time.time()

        with self._lock:
            entry = self._store.get(key)

            if not entry:
                return None

            expires_at, embedding = entry

            if expires_at <= now:
                del self._store[key]
                return None

            return list(embedding)

    def set(self, text: str, embedding: list[float]) -> None:
        key = self._key(text)
        expires_at = time.time() + self.ttl_seconds

        with self._lock:
            if len(self._store) >= self.max_entries:
                self._evict_oldest()

            self._store[key] = (expires_at, list(embedding))

    def _evict_oldest(self) -> None:
        if not self._store:
            return

        oldest_key = min(self._store, key=lambda item: self._store[item][0])
        del self._store[oldest_key]

    def _key(self, text: str) -> str:
        normalized = " ".join(str(text or "").split())[:4000]
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
