from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.domain.services.sql_query_telemetry_models import SqlQueryRecord


def _aggregate_by_hash(entries: list[SqlQueryRecord]) -> list[dict[str, Any]]:
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

    return aggregated


def _aggregate_by_operation_id(entries: list[SqlQueryRecord]) -> list[dict[str, Any]]:
    by_operation: dict[str, dict[str, Any]] = {}

    for item in entries:
        key = item.operation_id or ""
        bucket = by_operation.setdefault(
            key,
            {
                "operation_id": item.operation_id,
                "label": item.operation_id or "—",
                "count": 0,
                "total_ms": 0.0,
                "max_ms": 0.0,
                "distinct_queries": set(),
                "last_caller_app": item.caller_app,
                "last_recorded_at": item.recorded_at,
            },
        )
        bucket["count"] += 1
        bucket["total_ms"] += item.duration_ms
        bucket["max_ms"] = max(bucket["max_ms"], item.duration_ms)
        bucket["distinct_queries"].add(item.query_hash)
        bucket["last_caller_app"] = item.caller_app
        bucket["last_recorded_at"] = item.recorded_at

    aggregated = []
    for bucket in by_operation.values():
        count = bucket["count"]
        distinct_queries = bucket.pop("distinct_queries")
        aggregated.append(
            {
                **bucket,
                "query_count": len(distinct_queries),
                "avg_ms": round(bucket["total_ms"] / count, 2),
                "total_ms": round(bucket["total_ms"], 2),
            }
        )

    return sorted(aggregated, key=lambda row: row["count"], reverse=True)


def build_sql_health_payload(
    entries: list[SqlQueryRecord],
    *,
    limit: int,
    storage_backend: str,
    filter_operation_id: str | None = None,
) -> dict[str, Any]:
    if not entries:
        payload: dict[str, Any] = {
            "storage_backend": storage_backend,
            "total_samples": 0,
            "window_samples": 0,
            "top_by_duration": [],
            "top_by_count": [],
            "by_operation_id": [],
            "recent": [],
        }
        if filter_operation_id is not None:
            payload["filter_operation_id"] = filter_operation_id
            payload["timeline"] = []
            payload["queries_in_operation"] = []
        return payload

    aggregated = _aggregate_by_hash(entries)
    top_by_duration = sorted(aggregated, key=lambda row: row["max_ms"], reverse=True)[:limit]
    top_by_count = sorted(aggregated, key=lambda row: row["count"], reverse=True)[:limit]
    by_operation_id = _aggregate_by_operation_id(entries)[:limit]
    recent = [asdict(item) for item in reversed(entries[-limit:])]

    payload = {
        "storage_backend": storage_backend,
        "total_samples": len(entries),
        "window_samples": len(entries),
        "top_by_duration": top_by_duration,
        "top_by_count": top_by_count,
        "by_operation_id": by_operation_id,
        "recent": recent,
    }

    if filter_operation_id is not None:
        payload["filter_operation_id"] = filter_operation_id
        payload["timeline"] = [
            {
                "recorded_at": item.recorded_at,
                "duration_ms": item.duration_ms,
                "query_hash": item.query_hash,
                "preview": item.preview,
                "caller_app": item.caller_app,
                "repository": item.repository,
            }
            for item in entries[-limit:]
        ]
        payload["queries_in_operation"] = top_by_count

    return payload


def filter_entries_by_operation_id(
    entries: list[SqlQueryRecord],
    operation_id: str | None,
) -> list[SqlQueryRecord]:
    if operation_id is None:
        return entries

    if operation_id == "__none__":
        return [item for item in entries if not item.operation_id]

    return [item for item in entries if item.operation_id == operation_id]
