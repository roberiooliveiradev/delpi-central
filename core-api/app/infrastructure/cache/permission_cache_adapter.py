# app/infrastructure/cache/permission_cache_adapter.py


from typing import List, Optional
from app.domain.ports.cache_port import PermissionCachePort


class InMemoryPermissionCache(PermissionCachePort):

    def __init__(self):
        self._store: dict[str, List[str]] = {}

    def get(self, user_id: str) -> Optional[List[str]]:
        return self._store.get(user_id)

    def set(self, user_id: str, permissions: List[str]) -> None:
        self._store[user_id] = permissions

    def invalidate(self, user_id: str) -> None:
        self._store.pop(user_id, None)