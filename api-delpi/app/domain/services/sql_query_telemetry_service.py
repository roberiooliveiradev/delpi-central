"""Telemetria de queries SQL — ring buffer em memória (Fase 2 do console)."""

from __future__ import annotations

import hashlib
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from app.infrastructure.observability.request_context import get_caller_app, get_operation_id

_MAX_ENTRIES = 800
_PREVIEW_LEN = 160


@dataclass(frozen=True)
class SqlQueryRecord:
    query_hash: str
    duration_ms: float
    operation_id: str | None
    caller_app: str | None
    repository: str
    recorded_at: str
    preview: str


_lock = threading.Lock()
_buffer: deque[SqlQueryRecord] = deque(maxlen=_MAX_ENTRIES)


def _normalize_query(query: str) -> str:
    return " ".join(query.split())


def query_hash(query: str) -> str:
    normalized = _normalize_query(query).lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def _preview(query: str) -> str:
    compact = _normalize_query(query)
    if len(compact) <= _PREVIEW_LEN:
        return compact
    return compact[: _PREVIEW_LEN - 1] + "…"


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
        preview=_preview(query),
    )

    with _lock:
        _buffer.append(record)


def get_sql_health_summary(*, limit: int = 25) -> dict[str, Any]:
    with _lock:
        entries = list(_buffer)

    if not entries:
        return {
            "total_samples": 0,
            "window_samples": 0,
            "top_by_duration": [],
            "top_by_count": [],
            "recent": [],
        }

    by_hash: dict[str, dict[str, Any]] = {}

    for item in entries:
        bucket = by_hash.setdefault(
            item.query_hash,
            {
                "query_hash": item.query_hash,
                "preview": item.preview,
                "count": 0,
                "total_ms": 0.0,
                "max_ms": 0.0,
                "last_operation_id": item.operation_id,
                "last_caller_app": item.caller_app,
                "last_repository": item.repository,
                "last_recorded_at": item.recorded_at,
            },
        )
        bucket["count"] += 1
        bucket["total_ms"] += item.duration_ms
        bucket["max_ms"] = max(bucket["max_ms"], item.duration_ms)
        bucket["last_operation_id"] = item.operation_id
        bucket["last_caller_app"] = item.caller_app
        bucket["last_repository"] = item.repository
        bucket["last_recorded_at"] = item.recorded_at

    aggregated = []
    for bucket in by_hash.values():
        count = bucket["count"]
        aggregated.append(
            {
                **bucket,
                "avg_ms": round(bucket["total_ms"] / count, 2),
                "total_ms": round(bucket["total_ms"], 2),
            }
        )

    top_by_duration = sorted(aggregated, key=lambda row: row["max_ms"], reverse=True)[:limit]
    top_by_count = sorted(aggregated, key=lambda row: row["count"], reverse=True)[:limit]
    recent = [asdict(item) for item in reversed(entries[-limit:])]

    return {
        "total_samples": len(entries),
        "window_samples": len(entries),
        "top_by_duration": top_by_duration,
        "top_by_count": top_by_count,
        "recent": recent,
    }


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
