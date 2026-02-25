# app/infrastructure/cache/rbac_permission_cache_adapter.py

from typing import Optional, List
from app.domain.ports.cache_port import PermissionCachePort
from app.infrastructure.security.rbac_cache import rbac_cache


class RbacCachePermissionCacheAdapter(PermissionCachePort):
    def get(self, user_id: str) -> Optional[List[str]]:
        return rbac_cache.get(user_id)

    def set(self, user_id: str, permissions: List[str]) -> None:
        rbac_cache.set(user_id, permissions)

    def invalidate(self, user_id: str) -> None:
        rbac_cache.invalidate(user_id)