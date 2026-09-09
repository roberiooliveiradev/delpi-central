from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import JSONResponse

from production_pulse_app.application.services.firmware_catalog_service import (
    FirmwareCatalogService,
    message_for_firmware_error,
)
from production_pulse_app.application.services.firmware_update_job_service import (
    FirmwareUpdateJobService,
)
from production_pulse_app.core.responses import error, success
from production_pulse_app.domain.errors import ContentCodedError, DeviceValidationError
from production_pulse_app.infrastructure.content.firmware_ota_messages_content_service import (
    firmware_ota_http_message,
)
from production_pulse_app.infrastructure.persistence.repositories.postgres_firmware_repository import (
    FirmwareJobNotFoundError,
    FirmwareNotFoundError,
)
from production_pulse_app.interface.http.rbac_http import (
    guard_branch_access,
    guard_manage_devices,
    guard_view_devices,
)

router = APIRouter(tags=["FirmwareOTA"])
_catalog = FirmwareCatalogService()
_jobs = FirmwareUpdateJobService()


def _actor_sub(request: Request) -> str | None:
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return getattr(user, "sub", None) or getattr(user, "id", None)


def _coded_error(exc: ContentCodedError) -> JSONResponse:
    payload = error(
        message_for_firmware_error(exc.code),
        code=exc.code,
        status_code=422,
    )
    status_code = payload.pop("_status_code", 422)
    return JSONResponse(status_code=status_code, content=payload)


@router.get("/firmwares")
async def list_firmwares(
    request: Request,
    firmwareKey: str | None = Query(default=None),
    driverKey: str | None = Query(default=None),
    includeArchived: bool = Query(default=True),
    publishedOnly: bool = Query(default=False),
):
    denied = guard_view_devices(request)
    if denied:
        return denied
    items = _catalog.list_firmwares(
        firmware_key=firmwareKey,
        driver_key=driverKey,
        include_archived=includeArchived,
        published_only=publishedOnly,
    )
    return success({"items": items})


@router.get("/firmwares/{firmware_id}")
async def get_firmware(request: Request, firmware_id: str):
    denied = guard_view_devices(request)
    if denied:
        return denied
    try:
        data = _catalog.get_firmware(UUID(firmware_id))
    except (ValueError, FirmwareNotFoundError):
        payload = error(
            firmware_ota_http_message("firmwareNotFound"),
            code="firmwareNotFound",
            status_code=404,
        )
        return JSONResponse(status_code=404, content={k: v for k, v in payload.items() if k != "_status_code"})
    return success(data)


@router.patch("/firmwares/{firmware_id}")
async def patch_firmware(request: Request, firmware_id: str):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    body = await request.json()
    if not isinstance(body, dict):
        payload = error("Dados inválidos.", code="validation_error", status_code=422)
        return JSONResponse(status_code=422, content={k: v for k, v in payload.items() if k != "_status_code"})
    try:
        data = _catalog.update_metadata(
            UUID(firmware_id),
            display_name=body.get("displayName") if "displayName" in body else None,
            release_notes=body.get("releaseNotes") if "releaseNotes" in body else None,
        )
    except ContentCodedError as exc:
        return _coded_error(exc)
    except (ValueError, FirmwareNotFoundError):
        payload = error(
            firmware_ota_http_message("firmwareNotFound"),
            code="firmwareNotFound",
            status_code=404,
        )
        return JSONResponse(status_code=404, content={k: v for k, v in payload.items() if k != "_status_code"})
    return success(data)


@router.post("/firmwares/{firmware_id}/archive")
async def archive_firmware(request: Request, firmware_id: str):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        data = _catalog.archive(UUID(firmware_id))
    except (ValueError, FirmwareNotFoundError):
        payload = error(
            firmware_ota_http_message("firmwareNotFound"),
            code="firmwareNotFound",
            status_code=404,
        )
        return JSONResponse(status_code=404, content={k: v for k, v in payload.items() if k != "_status_code"})
    return success(data)


@router.get("/firmware-drivers")
async def list_firmware_drivers(request: Request):
    denied = guard_view_devices(request)
    if denied:
        return denied
    from production_pulse_app.application.services.device_driver_registry_service import (
        get_device_driver_registry,
    )

    items = get_device_driver_registry().list_catalog_drivers()
    return success({"items": items})


@router.post("/firmwares")
async def publish_firmware(
    request: Request,
    file: UploadFile = File(...),
    firmwareKey: str = Form(...),
    driverKey: str = Form(...),
    version: str = Form(...),
    displayName: str = Form(""),
    releaseNotes: str = Form(""),
    minCompatibleVersion: str = Form(""),
    publish: bool = Form(True),
):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    raw = await file.read()
    try:
        data = _catalog.publish(
            firmware_key=firmwareKey,
            driver_key=driverKey,
            version=version,
            display_name=displayName,
            raw=raw,
            filename_hint=file.filename,
            release_notes=releaseNotes or None,
            min_compatible_version=minCompatibleVersion or None,
            publish=publish,
            actor_sub=_actor_sub(request),
        )
    except ContentCodedError as exc:
        return _coded_error(exc)
    payload = success(data)
    return JSONResponse(status_code=201, content=payload)


@router.get("/firmware-update-jobs")
async def list_jobs(request: Request, branch: str | None = Query(default=None)):
    denied = guard_view_devices(request)
    if denied:
        return denied
    if branch:
        denied_branch = guard_branch_access(request, branch)
        if denied_branch:
            return denied_branch
    try:
        items = _jobs.list_jobs(branch=branch)
    except DeviceValidationError as exc:
        return _coded_error(ContentCodedError(exc.code))
    return success({"items": items})


@router.post("/firmware-update-jobs")
async def create_job(request: Request):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    body = await request.json()
    if not isinstance(body, dict):
        payload = error("Dados inválidos.", code="validation_error", status_code=422)
        return JSONResponse(status_code=422, content={k: v for k, v in payload.items() if k != "_status_code"})
    branch = str(body.get("branch") or "")
    denied_branch = guard_branch_access(request, branch)
    if denied_branch:
        return denied_branch
    try:
        data = _jobs.create_job(body, actor_sub=_actor_sub(request))
    except ContentCodedError as exc:
        return _coded_error(exc)
    except FirmwareNotFoundError:
        payload = error(
            firmware_ota_http_message("firmwareNotFound"),
            code="firmwareNotFound",
            status_code=404,
        )
        return JSONResponse(status_code=404, content={k: v for k, v in payload.items() if k != "_status_code"})
    except DeviceValidationError as exc:
        return _coded_error(ContentCodedError(exc.code))
    return JSONResponse(status_code=201, content=success(data))


@router.get("/firmware-update-jobs/{job_id}/targets")
async def list_targets(request: Request, job_id: str):
    denied = guard_view_devices(request)
    if denied:
        return denied
    try:
        items = _jobs.list_targets(UUID(job_id))
    except (ValueError, FirmwareJobNotFoundError):
        payload = error(
            firmware_ota_http_message("jobNotFound"),
            code="jobNotFound",
            status_code=404,
        )
        return JSONResponse(status_code=404, content={k: v for k, v in payload.items() if k != "_status_code"})
    return success({"items": items})


@router.post("/firmware-update-jobs/{job_id}/cancel")
async def cancel_job(request: Request, job_id: str):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        data = _jobs.cancel_job(UUID(job_id))
    except ContentCodedError as exc:
        return _coded_error(exc)
    except (ValueError, FirmwareJobNotFoundError):
        payload = error(
            firmware_ota_http_message("jobNotFound"),
            code="jobNotFound",
            status_code=404,
        )
        return JSONResponse(status_code=404, content={k: v for k, v in payload.items() if k != "_status_code"})
    return success(data)


@router.get("/firmware-update-summary")
async def firmware_update_summary(
    request: Request,
    branch: str = Query(...),
    firmwareKey: str | None = Query(default=None),
):
    denied = guard_view_devices(request)
    if denied:
        return denied
    denied_branch = guard_branch_access(request, branch)
    if denied_branch:
        return denied_branch
    try:
        data = _jobs.summary(branch=branch, firmware_key=firmwareKey)
    except DeviceValidationError as exc:
        return _coded_error(ContentCodedError(exc.code))
    return success(data)
