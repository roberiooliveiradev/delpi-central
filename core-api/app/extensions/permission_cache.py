import time

# Cache simples em memória
_permission_cache = {}

CACHE_TTL_SECONDS = 60  # 1 minuto (ajuste conforme necessidade)


def get_cached_permissions(user_id: str):
    entry = _permission_cache.get(user_id)
    if not entry:
        return None

    expires_at = entry["expires_at"]
    if time.time() > expires_at:
        _permission_cache.pop(user_id, None)
        return None

    return entry["permissions"]


def set_cached_permissions(user_id: str, permissions: list[str]):
    _permission_cache[user_id] = {
        "permissions": permissions,
        "expires_at": time.time() + CACHE_TTL_SECONDS,
    }


def invalidate_user_permissions(user_id: str):
    _permission_cache.pop(user_id, None)
