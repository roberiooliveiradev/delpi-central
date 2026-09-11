from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.responses import JSONResponse

from production_pulse_app.application.services.firmware_catalog_service import (
    FirmwareCatalogService,
    message_for_firmware_error,
)
from production_pulse_app.application.services.firmware_deletion_service import (
    FirmwareDeletionService,
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
_deletion = FirmwareDeletionService()
_jobs = FirmwareUpdateJobService()

_DELETION_CONFLICT_CODES = frozenset(
    {
        "firmwareHasUpdateHistory",
        "firmwareHasActiveTargets",
        "firmwareInstalledOnDevices",
        "deleteDependencyConflict",
    }
)


def _actor_sub(request: Request) -> str | None:
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return getattr(user, "sub", None) or getattr(user, "id", None)


def _coded_error(exc: ContentCodedError) -> JSONResponse:
    status = 409 if exc.code in _DELETION_CONFLICT_CODES else 422
    payload = error(
        message_for_firmware_error(exc.code),
        code=exc.code,
        status_code=status,
    )
    status_code = payload.pop("_status_code", status)
    return JSONResponse(status_code=status_code, content=payload)


def _not_found_firmware() -> JSONResponse:
    payload = error(
        firmware_ota_http_message("firmwareNotFound"),
        code="firmwareNotFound",
        status_code=404,
    )
    return JSONResponse(status_code=404, content={k: v for k, v in payload.items() if k != "_status_code"})


def _not_found_firmware_family() -> JSONResponse:
    payload = error(
        firmware_ota_http_message("firmwareFamilyNotFound"),
        code="firmwareFamilyNotFound",
        status_code=404,
    )
    return JSONResponse(status_code=404, content={k: v for k, v in payload.items() if k != "_status_code"})


@router.get("/firmwares", operation_id="list_firmwares")
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


@router.get("/firmwares/{firmware_id}", operation_id="get_firmware")
async def get_firmware(request: Request, firmware_id: str):
    denied = guard_view_devices(request)
    if denied:
        return denied
    try:
        data = _catalog.get_firmware(UUID(firmware_id))
    except (ValueError, FirmwareNotFoundError):
        return _not_found_firmware()
    return success(data)


@router.patch("/firmwares/{firmware_id}", operation_id="patch_firmware")
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
            source_text=body.get("sourceText") if "sourceText" in body else None,
            source_text_provided="sourceText" in body,
        )
    except ContentCodedError as exc:
        return _coded_error(exc)
    except (ValueError, FirmwareNotFoundError):
        return _not_found_firmware()
    return success(data)


@router.post("/firmwares/{firmware_id}/artifact", operation_id="attach_firmware_artifact")
async def attach_firmware_artifact(
    request: Request,
    firmware_id: str,
    file: UploadFile = File(...),
):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    raw = await file.read()
    try:
        data = _catalog.attach_artifact(
            UUID(firmware_id),
            raw=raw,
            filename_hint=file.filename,
        )
    except ContentCodedError as exc:
        return _coded_error(exc)
    except (ValueError, FirmwareNotFoundError):
        return _not_found_firmware()
    return success(data)


@router.post("/firmwares/{firmware_id}/publish", operation_id="publish_firmware_version")
async def publish_firmware_version(request: Request, firmware_id: str):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        data = _catalog.publish_version(UUID(firmware_id))
    except ContentCodedError as exc:
        return _coded_error(exc)
    except (ValueError, FirmwareNotFoundError):
        return _not_found_firmware()
    return success(data)


@router.post("/firmwares/{firmware_id}/archive", operation_id="archive_firmware")
async def archive_firmware(request: Request, firmware_id: str):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        data = _catalog.archive(UUID(firmware_id))
    except (ValueError, FirmwareNotFoundError):
        return _not_found_firmware()
    return success(data)


@router.get("/firmwares/{firmware_id}/deletion-impact", operation_id="get_firmware_deletion_impact")
async def get_firmware_deletion_impact(request: Request, firmware_id: str):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        return success(_deletion.get_deletion_impact(UUID(firmware_id)))
    except (ValueError, FirmwareNotFoundError):
        return _not_found_firmware()


@router.delete("/firmwares/{firmware_id}", operation_id="delete_firmware_permanently")
async def delete_firmware_permanently(request: Request, firmware_id: str):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        return success(
            _deletion.delete_permanently(
                UUID(firmware_id),
                actor_sub=_actor_sub(request),
            )
        )
    except ContentCodedError as exc:
        return _coded_error(exc)
    except (ValueError, FirmwareNotFoundError):
        return _not_found_firmware()


@router.get(
    "/firmware-families/{firmware_key}/deletion-impact",
    operation_id="get_firmware_family_deletion_impact",
)
async def get_firmware_family_deletion_impact(request: Request, firmware_key: str):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        return success(_deletion.get_family_deletion_impact(firmware_key))
    except FirmwareNotFoundError:
        return _not_found_firmware_family()


@router.delete(
    "/firmware-families/{firmware_key}",
    operation_id="delete_firmware_family_permanently",
)
async def delete_firmware_family_permanently(request: Request, firmware_key: str):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    try:
        return success(
            _deletion.delete_family_permanently(
                firmware_key,
                actor_sub=_actor_sub(request),
            )
        )
    except ContentCodedError as exc:
        return _coded_error(exc)
    except FirmwareNotFoundError:
        return _not_found_firmware_family()


@router.get("/firmware-drivers", operation_id="list_firmware_drivers")
async def list_firmware_drivers(request: Request):
    denied = guard_view_devices(request)
    if denied:
        return denied
    from production_pulse_app.application.services.device_driver_registry_service import (
        get_device_driver_registry,
    )

    items = get_device_driver_registry().list_catalog_drivers()
    return success({"items": items})


@router.post("/firmwares", operation_id="create_firmware")
async def create_firmware(
    request: Request,
    firmwareKey: str = Form(...),
    driverKey: str = Form(...),
    version: str = Form(...),
    displayName: str = Form(""),
    releaseNotes: str = Form(""),
    minCompatibleVersion: str = Form(""),
    sourceText: str = Form(""),
    publish: bool = Form(True),
    file: UploadFile | None = File(default=None),
):
    denied = guard_manage_devices(request)
    if denied:
        return denied
    raw: bytes | None = None
    filename_hint: str | None = None
    if file is not None:
        raw = await file.read()
        filename_hint = file.filename
    if publish and not raw:
        return _coded_error(ContentCodedError("firmwareMissingArtifact"))
    try:
        data = _catalog.create_draft(
            firmware_key=firmwareKey,
            driver_key=driverKey,
            version=version,
            display_name=displayName,
            source_text=sourceText or None,
            raw=raw,
            filename_hint=filename_hint,
            release_notes=releaseNotes or None,
            min_compatible_version=minCompatibleVersion or None,
            publish=publish,
            actor_sub=_actor_sub(request),
        )
    except ContentCodedError as exc:
        return _coded_error(exc)
    payload = success(data)
    return JSONResponse(status_code=201, content=payload)


@router.get("/firmware-update-jobs", operation_id="list_firmware_update_jobs")
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


@router.post("/firmware-update-jobs", operation_id="create_firmware_update_job")
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


@router.get("/firmware-update-jobs/{job_id}/targets", operation_id="list_firmware_update_targets")
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


@router.post("/firmware-update-jobs/{job_id}/cancel", operation_id="cancel_firmware_update_job")
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


@router.get("/firmware-update-summary", operation_id="get_firmware_update_summary")
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
