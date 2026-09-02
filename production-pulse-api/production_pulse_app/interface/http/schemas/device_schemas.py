from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreateBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    branch: str
    ip_address: str = Field(alias="ipAddress")
    driver_key: str = Field(alias="driverKey")
    poll_interval_ms: int = Field(default=30_000, alias="pollIntervalMs", ge=500, le=300_000)
    enabled: bool = True


class DeviceReplaceBody(DeviceCreateBody):
    pass


class DevicePatchBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    branch: str | None = None
    ip_address: str | None = Field(default=None, alias="ipAddress")
    driver_key: str | None = Field(default=None, alias="driverKey")
    poll_interval_ms: int | None = Field(
        default=None,
        alias="pollIntervalMs",
        ge=500,
        le=300_000,
    )
    enabled: bool | None = None


def body_to_dict(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(by_alias=False, exclude_none=True)


class DeviceTestProbeBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    branch: str
    ip_address: str = Field(alias="ipAddress")
    driver_key: str = Field(alias="driverKey")
