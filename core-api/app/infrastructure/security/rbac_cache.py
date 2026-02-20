# app/infrastructure/security/rbac_service.py

from threading import RLock
from typing import Dict, List


class RBACCache:

    def __init__(self):
        self._lock = RLock()
        self._cache: Dict[str, List[str]] = {}

    # ======================================================
    # GET
    # ======================================================

    def get(self, user_id: str):
        with self._lock:
            return self._cache.get(user_id)

    # ======================================================
    # SET
    # ======================================================

    def set(self, user_id: str, permissions: List[str]):
        with self._lock:
            self._cache[user_id] = permissions

    # ======================================================
    # INVALIDATE USER
    # ======================================================

    def invalidate_user(self, user_id: str):
        with self._lock:
            self._cache.pop(user_id, None)

    # ======================================================
    # CLEAR ALL
    # ======================================================

    def clear(self):
        with self._lock:
            self._cache.clear()


# Singleton global
rbac_cache = RBACCache()