"""Snapshot unificado para comparador antes/depois de deploy."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.composition.query_cache_composer import (
    get_query_cache_backend_name,
    get_query_cache_storage,
)
from app.config import settings
from app.domain.services.caller_request_stats_service import get_caller_stats_summary
from app.domain.services.query_cache_stats_service import build_query_cache_stats_payload
from app.domain.services.sql_query_telemetry_service import get_sql_health_summary


def build_observability_snapshot(*, limit: int = 25) -> dict[str, Any]:
    ttl_seconds = float(settings.QUERY_CACHE_TTL_SECONDS or 300)
    storage = get_query_cache_storage()
    keys_by_namespace = storage.count_keys_by_namespace() if storage else {}

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "query_cache": build_query_cache_stats_payload(
            backend=get_query_cache_backend_name(),
            ttl_seconds=ttl_seconds,
            keys_by_namespace=keys_by_namespace,
        ),
        "caller_stats": get_caller_stats_summary(limit=limit),
        "sql_health": get_sql_health_summary(limit=limit),
    }
