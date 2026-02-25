# app/domain/ports/cache_port.py

from typing import Protocol, Optional, List


class PermissionCachePort(Protocol):

    def get(self, user_id: str) -> Optional[List[str]]:
        ...

    def set(self, user_id: str, permissions: List[str]) -> None:
        ...

    def invalidate(self, user_id: str) -> None:
        ...