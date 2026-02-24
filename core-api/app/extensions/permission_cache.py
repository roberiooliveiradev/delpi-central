import time

# Cache simples em memória
_permission_cache = {}

CACHE_TTL_SECONDS = 60  # 1 minuto (ajuste conforme necessidade)


def get_cached_permissions(user_id: str):
    return None

def set_cached_permissions(user_id: str, permissions: list[str]):
    pass

def invalidate_user_permissions(user_id: str):
    pass
