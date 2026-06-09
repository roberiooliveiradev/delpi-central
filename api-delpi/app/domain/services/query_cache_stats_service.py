"""Estatísticas de hits/miss do cache compartilhado (LMP, estoque)."""

from __future__ import annotations

import threading
from typing import Any


def cache_namespace_from_key(key: str) -> str:
    return key.split("|", 1)[0] if key else "unknown"


_lock = threading.Lock()
_namespace_stats: dict[str, dict[str, int]] = {}


def _bucket(namespace: str) -> dict[str, int]:
    return _namespace_stats.setdefault(
        namespace,
        {"hits": 0, "misses": 0, "sets": 0},
    )


def record_cache_get(key: str, *, hit: bool) -> None:
    namespace = cache_namespace_from_key(key)
    with _lock:
        bucket = _bucket(namespace)
        if hit:
            bucket["hits"] += 1
        else:
            bucket["misses"] += 1


def record_cache_set(key: str) -> None:
    namespace = cache_namespace_from_key(key)
    with _lock:
        _bucket(namespace)["sets"] += 1


def build_query_cache_stats_payload(
    *,
    backend: str,
    ttl_seconds: float,
    keys_by_namespace: dict[str, int] | None = None,
) -> dict[str, Any]:
    with _lock:
        namespaces = []
        total_hits = 0
        total_misses = 0
        total_sets = 0

        for namespace, bucket in sorted(_namespace_stats.items()):
            hits = bucket["hits"]
            misses = bucket["misses"]
            sets = bucket["sets"]
            lookups = hits + misses
            hit_rate = round((hits / lookups) * 100, 2) if lookups else 0.0
            namespaces.append(
                {
                    "namespace": namespace,
                    "hits": hits,
                    "misses": misses,
                    "sets": sets,
                    "lookups": lookups,
                    "hit_rate_pct": hit_rate,
                    "active_keys": (keys_by_namespace or {}).get(namespace, 0),
                }
            )
            total_hits += hits
            total_misses += misses
            total_sets += sets

        total_lookups = total_hits + total_misses
        return {
            "backend": backend,
            "ttl_seconds": ttl_seconds,
            "totals": {
                "hits": total_hits,
                "misses": total_misses,
                "sets": total_sets,
                "lookups": total_lookups,
                "hit_rate_pct": round((total_hits / total_lookups) * 100, 2)
                if total_lookups
                else 0.0,
            },
            "namespaces": namespaces,
        }


def reset_query_cache_stats_for_tests() -> None:
    with _lock:
        _namespace_stats.clear()
