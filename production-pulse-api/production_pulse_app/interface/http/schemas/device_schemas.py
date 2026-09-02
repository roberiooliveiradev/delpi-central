from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from production_pulse_app.infrastructure.content.device_validation_content_service import (
    poll_interval_default,
    poll_interval_max,
    poll_interval_min,
)

_POLL_MIN = poll_interval_min()
_POLL_MAX = poll_interval_max()
_POLL_DEFAULT = poll_interval_default()


class DeviceCreateBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    branch: str
    ip_address: str = Field(alias="ipAddress")
    driver_key: str = Field(alias="driverKey")
    controller_code: str | None = Field(default=None, alias="controllerCode")
    firmware_source: str | None = Field(default=None, alias="firmwareSource")
    wifi_ssid: str | None = Field(default=None, alias="wifiSsid")
    wifi_password: str | None = Field(default=None, alias="wifiPassword")
    debounce_ms: int | None = Field(default=None, alias="debounceMs")
    api_token: str | None = Field(default=None, alias="apiToken")
    poll_interval_ms: int = Field(
        default=_POLL_DEFAULT,
        alias="pollIntervalMs",
        ge=_POLL_MIN,
        le=_POLL_MAX,
    )
    enabled: bool = True


class DeviceReplaceBody(DeviceCreateBody):
    pass


class DevicePatchBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    branch: str | None = None
    ip_address: str | None = Field(default=None, alias="ipAddress")
    driver_key: str | None = Field(default=None, alias="driverKey")
    controller_code: str | None = Field(default=None, alias="controllerCode")
    firmware_source: str | None = Field(default=None, alias="firmwareSource")
    wifi_ssid: str | None = Field(default=None, alias="wifiSsid")
    wifi_password: str | None = Field(default=None, alias="wifiPassword")
    debounce_ms: int | None = Field(default=None, alias="debounceMs")
    api_token: str | None = Field(default=None, alias="apiToken")
    poll_interval_ms: int | None = Field(
        default=None,
        alias="pollIntervalMs",
        ge=_POLL_MIN,
        le=_POLL_MAX,
    )
    enabled: bool | None = None


def body_to_dict(model: BaseModel) -> dict[str, Any]:
    # Keep explicit nulls for write-only clears (apiToken "") — exclude_unset only
    return model.model_dump(by_alias=False, exclude_none=False, exclude_unset=True)


class DeviceTestProbeBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    branch: str
    ip_address: str = Field(alias="ipAddress")
    driver_key: str = Field(alias="driverKey")
