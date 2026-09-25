from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from delpi_auth.service_token import request_has_valid_internal_service_token

from production_pulse_app.application.services.integration_device_snapshot_service import (
    IntegrationDeviceSnapshotService,
)
from production_pulse_app.core.responses import error, success
from production_pulse_app.infrastructure.persistence.repositories.postgres_device_repository import (
    DeviceNotFoundError,
)
from production_pulse_app.interface.http.rbac_http import (
    guard_view_devices,
)

router = APIRouter(prefix="/integrations", tags=["Integrations"])

_snapshot_service = IntegrationDeviceSnapshotService()


def _guard_integration_read(request: Request) -> JSONResponse | None:
    """S2S interno ou usuário com devices.view."""
    if request_has_valid_internal_service_token(request):
        return None
    return guard_view_devices(request)


@router.get("/devices/snapshot", operation_id="get_production_pulse_devices_snapshot")
async def get_devices_snapshot(
    request: Request,
    branch: str = Query(..., min_length=2, max_length=2),
    workCenter: str = Query(..., min_length=1, max_length=40),
    roleKey: str | None = Query(default="pulse_counter"),
):
    denied = _guard_integration_read(request)
    if denied is not None:
        return denied
    try:
        payload = _snapshot_service.list_by_work_center(
            branch=branch,
            work_center=workCenter,
            role_key=roleKey,
        )
    except ValueError as exc:
        body = error(str(exc), code="validation_error", status_code=422)
        status = body.pop("_status_code", 422)
        return JSONResponse(status_code=status, content=body)
    return success(payload)


@router.get("/devices/{device_id}/snapshot", operation_id="get_production_pulse_device_snapshot")
async def get_device_snapshot(request: Request, device_id: UUID):
    denied = _guard_integration_read(request)
    if denied is not None:
        return denied
    try:
        payload = _snapshot_service.get_by_device_id(device_id)
    except DeviceNotFoundError:
        body = error("Dispositivo não encontrado.", code="not_found", status_code=404)
        status = body.pop("_status_code", 404)
        return JSONResponse(status_code=status, content=body)
    return success(payload)
