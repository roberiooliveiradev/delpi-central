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
    include_api_token: bool = False,
) -> dict[str, Any]:
    token_raw = str(row.get("device_api_token") or "").strip()
    # List queries mask presence as "1" — never treat that as a readable secret.
    token_readable = token_raw if token_raw and token_raw != "1" else ""
    payload = {
        "id": str(row["id"]),
        "branch": row["branch"],
        "name": row["name"],
        "ipAddress": str(row["ip_address"]),
        "controllerCode": row.get("controller_code"),
        "firmwareSource": row.get("firmware_source"),
        "wifiSsid": row.get("wifi_ssid"),
        "debounceMs": row.get("debounce_ms"),
        "apiTokenSet": bool(token_raw),
        "driverKey": row["driver_key"],
        "roleKey": row["role_key"],
        "firmwareKey": row.get("firmware_key") or row["driver_key"],
        "assignedFirmwareKey": row.get("firmware_key"),
        "installedFirmwareVersion": row.get("installed_firmware_version"),
        "targetFirmwareVersion": row.get("target_firmware_version"),
        "firmwareReportedAt": row.get("firmware_reported_at"),
        "lastOtaCheckAt": row.get("last_ota_check_at"),
        "enabled": row["enabled"],
        "pollIntervalMs": int(row["poll_interval_ms"]),
        "lastSeenAt": row.get("last_seen_at"),
        "lastPollAttemptAt": row.get("last_poll_attempt_at"),
        "nextPollAt": row.get("next_poll_at"),
        "lastMetrics": public_metrics(row.get("last_metrics") or {}),
        "lastError": row.get("last_error"),
        "ledState": row.get("led_state"),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
        "createdBy": row.get("created_by"),
        "updatedBy": row.get("updated_by"),
    }
    if include_api_token and token_readable:
        payload["apiToken"] = token_readable
    if capabilities is not None:
        payload["capabilities"] = capabilities
    return payload


def parse_device_id(device_id: str) -> UUID:
    return UUID(str(device_id))
