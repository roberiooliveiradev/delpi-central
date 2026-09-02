from __future__ import annotations

from typing import Any
from uuid import UUID

from production_pulse_app.domain.services.device_monotonic_counter_continuity_service import (
    public_metrics,
)


def device_row_to_api(
    row: dict[str, Any],
    *,
    capabilities: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "id": str(row["id"]),
        "branch": row["branch"],
        "name": row["name"],
        "ipAddress": str(row["ip_address"]),
        "controllerCode": row.get("controller_code"),
        "driverKey": row["driver_key"],
        "roleKey": row["role_key"],
        "enabled": row["enabled"],
        "pollIntervalMs": int(row["poll_interval_ms"]),
        "lastSeenAt": row.get("last_seen_at"),
        "lastPollAttemptAt": row.get("last_poll_attempt_at"),
        "nextPollAt": row.get("next_poll_at"),
        "lastMetrics": public_metrics(row.get("last_metrics") or {}),
        "lastError": row.get("last_error"),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
        "createdBy": row.get("created_by"),
        "updatedBy": row.get("updated_by"),
    }
    if capabilities is not None:
        payload["capabilities"] = capabilities
    return payload


def parse_device_id(device_id: str) -> UUID:
    return UUID(str(device_id))
