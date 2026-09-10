from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from production_pulse_app.application.services.device_driver_catalog_service import (
    DeviceDriverCatalogService,
)
from production_pulse_app.application.services.firmware_catalog_service import (
    message_for_firmware_error,
)
from production_pulse_app.core.responses import error, success
from production_pulse_app.domain.errors import ContentCodedError
from production_pulse_app.interface.http.rbac_http import (
    guard_manage_devices,
    guard_view_devices,
)

router = APIRouter(tags=["DeviceDrivers"])
_catalog = DeviceDriverCatalogService()


def _coded_error(exc: ContentCodedError) -> JSONResponse:
    payload = error(
        message_for_firmware_error(exc.code),
        code=exc.code,
        status_code=422,
    )
    status_code = payload.pop("_status_code", 422)
    return JSONResponse(status_code=status_code, content=payload)


class DriverCreateBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    driver_key: str = Field(alias="driverKey")
    protocol_kind: str = Field(alias="protocolKind")
    role_key: str | None = Field(default=None, alias="roleKey")
    label_pt: str = Field(alias="labelPt")
    description_pt: str | None = Field(default=None, alias="descriptionPt")
    metrics: list | None = None
    commands: list | None = None
    operator_surface: str | None = Field(default=None, alias="operatorSurface")
    operator_eligible: bool | None = Field(default=None, alias="operatorEligible")
    poll: dict | None = None
    thresholds: dict | None = None
    counter_restore: dict | None = Field(default=None, alias="counterRestore")


class DriverPatchBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role_key: str | None = Field(default=None, alias="roleKey")
    label_pt: str | None = Field(default=None, alias="labelPt")
    description_pt: str | None = Field(default=None, alias="descriptionPt")
    metrics: list | None = None
    commands: list | None = None
    operator_surface: str | None = Field(default=None, alias="operatorSurface")
    operator_eligible: bool | None = Field(default=None, alias="operatorEligible")
    poll: dict | None = None
    thresholds: dict | None = None
    counter_restore: dict | None = Field(default=None, alias="counterRestore")


@router.get("/drivers", operation_id="list_device_drivers")
async def list_device_drivers(
    request: Request,
    includeArchived: bool = Query(default=False),
):
    denied = guard_view_devices(request)
    if denied:
        return denied
    return success({"items": _catalog.list_drivers(include_archived=includeArchived)})


@router.get("/drivers/{driverKey}", operation_id="get_device_driver")
async def get_device_driver(request: Request, driverKey: str):
    denied = guard_view_devices(request)
    if denied:
        return denied
    try:
        return success(_catalog.get_driver(driverKey))
    except ContentCodedError as exc:
        return _coded_error(exc)


@router.post("/drivers", operation_id="create_device_driver")
async def create_device_driver(request: Request, body: DriverCreateBody):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        data = _catalog.create_driver(body.model_dump(by_alias=True, exclude_none=False))
    except ContentCodedError as exc:
        return _coded_error(exc)
    return JSONResponse(status_code=201, content=success(data))


@router.patch("/drivers/{driverKey}", operation_id="patch_device_driver")
async def patch_device_driver(request: Request, driverKey: str, body: DriverPatchBody):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        data = _catalog.update_driver(
            driverKey,
            body.model_dump(by_alias=True, exclude_none=True),
        )
    except ContentCodedError as exc:
        return _coded_error(exc)
    return success(data)


@router.post("/drivers/{driverKey}/archive", operation_id="archive_device_driver")
async def archive_device_driver(request: Request, driverKey: str):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        return success(_catalog.archive_driver(driverKey))
    except ContentCodedError as exc:
        return _coded_error(exc)


@router.post("/drivers/{driverKey}/unarchive", operation_id="unarchive_device_driver")
async def unarchive_device_driver(request: Request, driverKey: str):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        return success(_catalog.unarchive_driver(driverKey))
    except ContentCodedError as exc:
        return _coded_error(exc)
