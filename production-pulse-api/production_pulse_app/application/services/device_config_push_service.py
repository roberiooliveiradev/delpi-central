from __future__ import annotations

from typing import Any

from production_pulse_app.application.services.device_driver_registry_service import (
    DeviceDriverNotImplementedError,
    get_device_driver_registry,
)
from production_pulse_app.config import settings
from production_pulse_app.domain.services.device_config_payload_service import (
    build_configure_http_payload,
)
from production_pulse_app.infrastructure.content.device_api_messages_content_service import (
    device_config_push_message,
)


def resolve_device_ota_base_url() -> str:
    """Canonical OTA API base for IoT devices (no trailing slash)."""
    raw = (settings.PP_DEVICE_OTA_BASE_URL or "").strip()
    if raw:
        return raw.rstrip("/")
    # Fallback: PUBLIC_BASE_URL + API root (may be unreachable from shop floor — prefer PP_DEVICE_OTA_BASE_URL).
    public = (settings.PUBLIC_BASE_URL or "").strip().rstrip("/")
    root = (settings.PRODUCTION_PULSE_API_ROOT_PATH or "").strip()
    if not root.startswith("/"):
        root = f"/{root}" if root else ""
    if public:
        return f"{public}{root}".rstrip("/")
    return root.rstrip("/") if root else ""


class DeviceConfigPushService:
    """Best-effort POST /api/config after device save (mode A)."""

    def __init__(self) -> None:
        self._registry = get_device_driver_registry()

    def push_after_save(
        self,
        device_row: dict[str, Any],
        *,
        request_payload: dict[str, Any],
        force_ota_provision: bool = True,
    ) -> dict[str, Any]:
        configure_body = build_configure_http_payload(
            {
                "wifiSsid": request_payload.get("wifi_ssid")
                if "wifi_ssid" in request_payload
                else request_payload.get("wifiSsid"),
                "wifiPassword": request_payload.get("wifi_password")
                if "wifi_password" in request_payload
                else request_payload.get("wifiPassword"),
                "debounceMs": request_payload.get("debounce_ms")
                if "debounce_ms" in request_payload
                else request_payload.get("debounceMs"),
                "apiToken": request_payload.get("api_token")
                if "api_token" in request_payload
                else request_payload.get("apiToken"),
            }
        )
        # Also push persisted mirror fields when password omitted but ssid/debounce/token stored
        if "ssid" not in configure_body and device_row.get("wifi_ssid"):
            if "wifiSsid" in request_payload or "wifi_ssid" in request_payload:
                configure_body["ssid"] = str(device_row["wifi_ssid"])
        if "debounceMs" not in configure_body and device_row.get("debounce_ms") is not None:
            if "debounceMs" in request_payload or "debounce_ms" in request_payload:
                configure_body["debounceMs"] = int(device_row["debounce_ms"])
        if "apiToken" not in configure_body and device_row.get("device_api_token"):
            if "apiToken" in request_payload or "api_token" in request_payload:
                configure_body["apiToken"] = str(device_row["device_api_token"])

        if force_ota_provision:
            self._merge_ota_provision_fields(configure_body, device_row)

        if not configure_body:
            return {
                "status": "skipped",
                "message": device_config_push_message("skipped"),
            }

        driver_key = str(device_row.get("driver_key") or "")
        try:
            capabilities = self._registry.build_capabilities(driver_key)
        except Exception:
            return {
                "status": "skipped",
                "message": device_config_push_message("skipped"),
            }
        allowed = {str(item).strip().lower() for item in (capabilities.get("commands") or [])}
        if "configure" not in allowed:
            return {
                "status": "skipped",
                "message": device_config_push_message("skipped"),
            }

        try:
            driver = self._registry.get_implementation(driver_key)
        except DeviceDriverNotImplementedError:
            return {
                "status": "failed",
                "message": device_config_push_message("failed"),
            }

        result = driver.execute(device_row, "configure", payload=configure_body)
        if result.success:
            return {
                "status": "ok",
                "message": device_config_push_message("ok"),
                "response": result.response_payload or {},
            }
        return {
            "status": "failed",
            "message": device_config_push_message("failed"),
            "errorCode": result.error_code,
        }

    @staticmethod
    def _merge_ota_provision_fields(
        configure_body: dict[str, Any],
        device_row: dict[str, Any],
    ) -> None:
        ota_base = resolve_device_ota_base_url()
        if ota_base:
            configure_body["otaBaseUrl"] = ota_base
        branch = str(device_row.get("branch") or "").strip()
        if branch:
            configure_body["branch"] = branch
        interval = int(settings.PP_DEVICE_OTA_CHECK_INTERVAL_MS or 60000)
        if interval >= 1000:
            configure_body["otaCheckIntervalMs"] = interval


__all__ = ["DeviceConfigPushService", "resolve_device_ota_base_url"]
