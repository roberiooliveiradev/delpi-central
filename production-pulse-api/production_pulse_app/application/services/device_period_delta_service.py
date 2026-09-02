from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from production_pulse_app.domain.services.device_period_bounds_service import (
    resolve_day_bounds,
    resolve_shift_bounds,
)
from production_pulse_app.infrastructure.content.period_aggregation_content_service import (
    monotonic_metrics_for_role,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_reading_repository import (
    PostgresDeviceReadingRepository,
)


class DevicePeriodDeltaService:
    def __init__(
        self,
        reading_repository: PostgresDeviceReadingRepository | None = None,
    ) -> None:
        self._readings = reading_repository or PostgresDeviceReadingRepository()

    def build_period_deltas_for_devices(
        self,
        rows: list[dict[str, Any]],
        *,
        now: datetime | None = None,
    ) -> dict[UUID, dict[str, dict[str, int]]]:
        counter_rows = [row for row in rows if row.get("role_key") == "pulse_counter"]
        if not counter_rows:
            return {}

        metric_keys = monotonic_metrics_for_role("pulse_counter") or ["counter"]
        metric_key = metric_keys[0]
        device_ids = [row["id"] for row in counter_rows]
        current = now or datetime.now(timezone.utc)

        day_start, day_end = resolve_day_bounds(current)
        shift_start, shift_end = resolve_shift_bounds(current)

        day_sums = self._readings.sum_delta_metric_for_devices(
            device_ids,
            metric_key=metric_key,
            recorded_from=day_start,
            recorded_to=day_end,
        )
        shift_sums = self._readings.sum_delta_metric_for_devices(
            device_ids,
            metric_key=metric_key,
            recorded_from=shift_start,
            recorded_to=shift_end,
        )

        payload: dict[UUID, dict[str, dict[str, int]]] = {}
        for device_id in device_ids:
            payload[device_id] = {
                "day": {metric_key: int(day_sums.get(device_id, 0))},
                "shift": {metric_key: int(shift_sums.get(device_id, 0))},
            }
        return payload

    def aggregate_branch_counter_deltas(
        self,
        rows: list[dict[str, Any]],
        *,
        bound_device_ids: set[UUID],
        now: datetime | None = None,
    ) -> dict[str, dict[str, int]] | None:
        eligible = [
            row
            for row in rows
            if row.get("role_key") == "pulse_counter" and row["id"] in bound_device_ids
        ]
        if not eligible:
            return None

        per_device = self.build_period_deltas_for_devices(eligible, now=now)
        metric_keys = monotonic_metrics_for_role("pulse_counter") or ["counter"]
        metric_key = metric_keys[0]

        day_total = 0
        shift_total = 0
        for deltas in per_device.values():
            day_total += int((deltas.get("day") or {}).get(metric_key, 0))
            shift_total += int((deltas.get("shift") or {}).get(metric_key, 0))

        return {
            "day": {metric_key: day_total},
            "shift": {metric_key: shift_total},
        }


__all__ = ["DevicePeriodDeltaService"]
