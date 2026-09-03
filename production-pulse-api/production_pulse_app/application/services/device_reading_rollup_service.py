from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from production_pulse_app.infrastructure.content.telemetry_persistence_content_service import (
    rollup_enabled,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_reading_rollup_repository import (
    PostgresDeviceReadingRollupRepository,
    truncate_bucket_start,
)


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sum_delta_maps(
    previous: dict[str, Any] | None,
    incoming: dict[str, Any] | None,
) -> dict[str, Any]:
    left = previous if isinstance(previous, dict) else {}
    right = incoming if isinstance(incoming, dict) else {}
    keys = set(left.keys()) | set(right.keys())
    result: dict[str, Any] = {}
    for key in keys:
        a = _as_number(left.get(key))
        b = _as_number(right.get(key))
        if a is None and b is None:
            continue
        total = (a or 0.0) + (b or 0.0)
        result[key] = int(total) if float(total).is_integer() else total
    return result


def rollup_row_to_api(row: dict[str, Any]) -> dict[str, Any]:
    bucket = row.get("bucket_start")
    resolution = str(row.get("resolution") or "hour")
    return {
        "id": f"rollup:{resolution}:{row.get('id')}",
        "deviceId": str(row["device_id"]),
        "metrics": row.get("metrics") or {},
        "deltaMetrics": row.get("delta_metrics") or {},
        "meta": {
            "resolution": resolution,
            "samples": int(row.get("samples") or 0),
            "rollup": True,
        },
        "source": "rollup",
        "recordedAt": bucket,
        "createdAt": row.get("updated_at") or row.get("created_at"),
    }


class DeviceReadingRollupService:
    """R50 — mantém buckets hour/day a partir de readings persistidas."""

    def __init__(
        self,
        rollup_repository: PostgresDeviceReadingRollupRepository | None = None,
    ) -> None:
        self._rollups = rollup_repository or PostgresDeviceReadingRollupRepository()

    def apply_persisted_reading(
        self,
        device_id: UUID,
        *,
        recorded_at: datetime,
        metrics: dict[str, Any],
        delta_metrics: dict[str, Any] | None,
    ) -> None:
        if not rollup_enabled():
            return
        when = recorded_at
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        for resolution in ("hour", "day"):
            bucket = truncate_bucket_start(when, resolution)
            existing = self._rollups.get_bucket(
                device_id,
                resolution=resolution,
                bucket_start=bucket,
            )
            previous_delta = existing.get("delta_metrics") if existing else {}
            samples = int(existing.get("samples") or 0) + 1 if existing else 1
            self._rollups.upsert_bucket(
                device_id,
                resolution=resolution,
                bucket_start=bucket,
                metrics=dict(metrics or {}),
                delta_metrics=_sum_delta_maps(previous_delta, delta_metrics),
                samples=samples,
            )

    def list_rollups(
        self,
        device_id: UUID,
        *,
        resolution: str,
        page: int = 1,
        page_size: int = 20,
        recorded_from: datetime | None = None,
        recorded_to: datetime | None = None,
    ) -> dict[str, Any]:
        normalized = "day" if resolution == "day" else "hour"
        page = max(1, page)
        page_size = min(max(1, page_size), 500)
        rows, total = self._rollups.list_for_device(
            device_id,
            resolution=normalized,
            page=page,
            page_size=page_size,
            recorded_from=recorded_from,
            recorded_to=recorded_to,
        )
        return {
            "items": [rollup_row_to_api(row) for row in rows],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
            },
            "resolution": normalized,
        }
