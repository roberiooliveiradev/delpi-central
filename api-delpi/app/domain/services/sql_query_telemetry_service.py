"""Telemetria de queries SQL — ring buffer em memória ou Redis (Fase 2 do console)."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from typing import Any

from app.composition.sql_telemetry_composer import build_sql_telemetry_store
from app.domain.services.sql_health_aggregator import (
    build_sql_health_payload,
    filter_entries_by_operation_id,
)
from app.domain.services.sql_query_telemetry_models import SqlQueryRecord, preview_query
from app.infrastructure.observability.request_context import get_caller_app, get_operation_id


def query_hash(query: str) -> str:
    from app.domain.services.sql_query_telemetry_models import normalize_query

    normalized = normalize_query(query).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def record_sql_query(
    *,
    query: str,
    duration_ms: float,
    repository: str,
) -> None:
    record = SqlQueryRecord(
        query_hash=query_hash(query),
        duration_ms=round(duration_ms, 2),
        operation_id=get_operation_id(),
        caller_app=get_caller_app(),
        repository=repository,
        recorded_at=datetime.now(timezone.utc).isoformat(),
        preview=preview_query(query),
    )
    build_sql_telemetry_store().append(record)


def get_sql_health_summary(
    *,
    limit: int = 25,
    operation_id: str | None = None,
) -> dict[str, Any]:
    store = build_sql_telemetry_store()
    all_entries = store.list_entries()
    entries = filter_entries_by_operation_id(all_entries, operation_id)

    return build_sql_health_payload(
        entries,
        limit=limit,
        storage_backend=store.backend_name(),
        filter_operation_id=operation_id,
    )


class _TimedQuery:
    def __init__(self, repository: str, query: str):
        self._repository = repository
        self._query = query
        self._started = 0.0

    def __enter__(self):
        self._started = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        duration_ms = (time.perf_counter() - self._started) * 1000
        record_sql_query(
            query=self._query,
            duration_ms=duration_ms,
            repository=self._repository,
        )
        return False


def timed_sql_query(repository: str, query: str) -> _TimedQuery:
    return _TimedQuery(repository, query)
