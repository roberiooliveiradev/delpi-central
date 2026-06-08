from __future__ import annotations

from si_app.config import settings
from si_app.infrastructure.cache.ttl_cache import TtlCache

_lmp_summary_cache: TtlCache[dict[str, float | int]] = TtlCache(
    ttl_seconds=settings.SI_SNAPSHOT_CACHE_TTL_SECONDS,
)


def lmp_summary_cache_key(
    *,
    date_start: str | None,
    date_end: str | None,
    branch: str | None,
) -> str:
    return "|".join(
        [
            "lmp-summary",
            date_start or "",
            date_end or "",
            branch or "",
        ]
    )


def get_cached_lmp_summary(key: str) -> dict[str, float | int] | None:
    return _lmp_summary_cache.get(key)


def set_cached_lmp_summary(key: str, value: dict[str, float | int]) -> None:
    _lmp_summary_cache.set(key, value)


def invalidate_lmp_summary_cache() -> None:
    _lmp_summary_cache.invalidate_all()
