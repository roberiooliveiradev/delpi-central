"""Agregação de requests por X-Delpi-Caller-App (Fase 3 do console)."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

_MAX_ENTRIES = 2000


@dataclass(frozen=True)
class CallerRequestRecord:
    caller_app: str | None
    route_path: str
    operation_id: str | None
    status_code: int
    duration_ms: float
    recorded_at: str


_lock = threading.Lock()
_buffer: deque[CallerRequestRecord] = deque(maxlen=_MAX_ENTRIES)


def record_caller_request(
    *,
    caller_app: str | None,
    route_path: str,
    operation_id: str | None,
    status_code: int,
    duration_ms: float,
) -> None:
    record = CallerRequestRecord(
        caller_app=caller_app,
        route_path=route_path,
        operation_id=operation_id,
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
        recorded_at=datetime.now(timezone.utc).isoformat(),
    )
    with _lock:
        _buffer.append(record)


def get_caller_stats_summary(*, limit: int = 25) -> dict[str, Any]:
    with _lock:
        entries = list(_buffer)

    if not entries:
        return {
            "total_requests": 0,
            "by_caller": [],
            "by_route": [],
            "recent": [],
        }

    by_caller: dict[str, dict[str, Any]] = {}
    by_route: dict[str, dict[str, Any]] = {}

    for item in entries:
        caller_key = item.caller_app or "(sem caller)"
        caller_bucket = by_caller.setdefault(
            caller_key,
            {
                "caller_app": item.caller_app,
                "label": item.caller_app or "—",
                "count": 0,
                "total_ms": 0.0,
                "max_ms": 0.0,
                "routes": set(),
                "errors": 0,
            },
        )
        caller_bucket["count"] += 1
        caller_bucket["total_ms"] += item.duration_ms
        caller_bucket["max_ms"] = max(caller_bucket["max_ms"], item.duration_ms)
        caller_bucket["routes"].add(item.route_path)
        if item.status_code >= 400:
            caller_bucket["errors"] += 1

        route_bucket = by_route.setdefault(
            item.route_path,
            {
                "route_path": item.route_path,
                "count": 0,
                "total_ms": 0.0,
                "callers": set(),
                "errors": 0,
            },
        )
        route_bucket["count"] += 1
        route_bucket["total_ms"] += item.duration_ms
        route_bucket["callers"].add(caller_key)
        if item.status_code >= 400:
            route_bucket["errors"] += 1

    callers = []
    for bucket in by_caller.values():
        count = bucket["count"]
        routes = bucket.pop("routes")
        callers.append(
            {
                **bucket,
                "route_count": len(routes),
                "avg_ms": round(bucket["total_ms"] / count, 2),
                "total_ms": round(bucket["total_ms"], 2),
            }
        )

    routes = []
    for bucket in by_route.values():
        count = bucket["count"]
        callers_set = bucket.pop("callers")
        routes.append(
            {
                **bucket,
                "caller_count": len(callers_set),
                "avg_ms": round(bucket["total_ms"] / count, 2),
                "total_ms": round(bucket["total_ms"], 2),
            }
        )

    by_caller_sorted = sorted(callers, key=lambda row: row["count"], reverse=True)[:limit]
    by_route_sorted = sorted(routes, key=lambda row: row["count"], reverse=True)[:limit]
    recent = [asdict(item) for item in reversed(entries[-limit:])]

    return {
        "total_requests": len(entries),
        "by_caller": by_caller_sorted,
        "by_route": by_route_sorted,
        "recent": recent,
    }


def reset_caller_request_stats_for_tests() -> None:
    with _lock:
        _buffer.clear()
