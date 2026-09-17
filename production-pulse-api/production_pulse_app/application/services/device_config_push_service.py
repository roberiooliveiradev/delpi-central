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
from production_pulse_app.infrastructure.drivers.device_http_support import (
    resolve_device_api_token,
)


def _norm_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _norm_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _payload_get(payload: dict[str, Any], snake: str, camel: str) -> Any:
    if snake in payload:
        return payload.get(snake)
    if camel in payload:
        return payload.get(camel)
    return None


def _payload_has(payload: dict[str, Any], snake: str, camel: str) -> bool:
    return snake in payload or camel in payload


def request_changes_chip_config(
    device_row: dict[str, Any],
    request_payload: dict[str, Any] | None,
) -> bool:
    """True when the save intends to change chip-side config (not Pulse-only fields).

    The MFE re-sends wifiSsid/debounce/branch on every edit; compare to the persisted
    row so poll/name/enabled updates do not POST /api/config.
    """
    if not isinstance(request_payload, dict) or not request_payload:
        return False

    # Write-only secrets: present + non-empty means operator set a new value.
    if _payload_has(request_payload, "api_token", "apiToken"):
        token = _payload_get(request_payload, "api_token", "apiToken")
        if token is not None and str(token).strip():
            return True

    if _payload_has(request_payload, "wifi_password", "wifiPassword"):
        password = _payload_get(request_payload, "wifi_password", "wifiPassword")
        if password is not None and str(password) != "":
            return True

    if _payload_has(request_payload, "wifi_ssid", "wifiSsid"):
        new_ssid = _norm_str(_payload_get(request_payload, "wifi_ssid", "wifiSsid"))
        old_ssid = _norm_str(device_row.get("wifi_ssid"))
        if new_ssid != old_ssid:
            return True

    if _payload_has(request_payload, "debounce_ms", "debounceMs"):
        new_debounce = _norm_int(_payload_get(request_payload, "debounce_ms", "debounceMs"))
        old_debounce = _norm_int(device_row.get("debounce_ms"))
        if new_debounce != old_debounce:
            return True

    if "branch" in request_payload:
        new_branch = _norm_str(request_payload.get("branch"))
        old_branch = _norm_str(device_row.get("branch"))
        if new_branch != old_branch:
            return True

    # Hardware identity / target host change → re-provision chip (incl. token).
    if _payload_has(request_payload, "controller_code", "controllerCode"):
        new_code = _norm_str(
            _payload_get(request_payload, "controller_code", "controllerCode")
        )
        old_code = _norm_str(device_row.get("controller_code"))
        if new_code != old_code:
            return True

    if _payload_has(request_payload, "ip_address", "ipAddress"):
        new_ip = _norm_str(_payload_get(request_payload, "ip_address", "ipAddress"))
        old_ip = _norm_str(device_row.get("ip_address"))
        if new_ip != old_ip:
            return True

    return False


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
    """Best-effort POST /api/config after save when chip config actually changes (or create)."""

    def __init__(self) -> None:
        self._registry = get_device_driver_registry()

    def push_after_save(
        self,
        device_row: dict[str, Any],
        *,
        request_payload: dict[str, Any],
        force_ota_provision: bool = False,
        previous_row: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        baseline = previous_row if previous_row is not None else device_row
        chip_changed = request_changes_chip_config(baseline, request_payload)
        # Poll/name/enabled-only (and unchanged wifi/debounce echoes) stay in Postgres.
        if not chip_changed and not force_ota_provision:
            return {
                "status": "skipped",
                "message": device_config_push_message("skipped_pulse_only"),
            }

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
        # Also push persisted mirror fields when password omitted but ssid/debounce stored
        if "ssid" not in configure_body and device_row.get("wifi_ssid"):
            if "wifiSsid" in request_payload or "wifi_ssid" in request_payload:
                configure_body["ssid"] = str(device_row["wifi_ssid"])
        if "debounceMs" not in configure_body and device_row.get("debounce_ms") is not None:
            if "debounceMs" in request_payload or "debounce_ms" in request_payload:
                configure_body["debounceMs"] = int(device_row["debounce_ms"])
        # Re-provision / create: always send persisted cadastro token when pushing.
        if "apiToken" not in configure_body:
            persisted_token = resolve_device_api_token(device_row)
            if persisted_token:
                configure_body["apiToken"] = persisted_token

        # OTA provision on create, or whenever chip config actually changes.
        if force_ota_provision or chip_changed:
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

        error_code = str(result.error_code or "http_error").strip() or "http_error"
        if error_code == "unauthorized" and resolve_device_api_token(device_row) is None:
            error_code = "missing_token"

        return {
            "status": "failed",
            "message": device_config_push_message("failed", error_code=error_code),
            "errorCode": error_code,
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


__all__ = [
    "DeviceConfigPushService",
    "request_changes_chip_config",
    "resolve_device_ota_base_url",
]
