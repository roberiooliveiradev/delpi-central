from __future__ import annotations

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import FileResponse, JSONResponse

from production_pulse_app.application.services.device_ota_service import (
    DeviceOtaAuthError,
    DeviceOtaService,
)
from production_pulse_app.core.responses import error, success
from production_pulse_app.domain.errors import ContentCodedError
from production_pulse_app.infrastructure.content.firmware_ota_messages_content_service import (
    firmware_ota_http_message,
)

router = APIRouter(prefix="/device-ota", tags=["DeviceOTA"])
_service = DeviceOtaService()


def _optional_int(value) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _auth_error() -> JSONResponse:
    payload = error(
        firmware_ota_http_message("deviceOtaUnauthorized"),
        code="deviceOtaUnauthorized",
        status_code=401,
    )
    return JSONResponse(
        status_code=401,
        content={k: v for k, v in payload.items() if k != "_status_code"},
    )


def _coded(exc: ContentCodedError, *, status_code: int = 422) -> JSONResponse:
    payload = error(
        firmware_ota_http_message(exc.code),
        code=exc.code,
        status_code=status_code,
    )
    return JSONResponse(
        status_code=status_code,
        content={k: v for k, v in payload.items() if k != "_status_code"},
    )


def _authenticate(
    *,
    x_device_token: str | None,
    device_id: str | None,
    controller_code: str | None,
    branch: str | None,
):
    try:
        return _service.authenticate_device(
            token=x_device_token,
            device_id=device_id,
            controller_code=controller_code,
            branch=branch,
        )
    except DeviceOtaAuthError:
        return None


@router.get("/check")
async def device_ota_check(
    deviceId: str | None = Query(default=None),
    controllerCode: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    x_device_token: str | None = Header(default=None, alias="X-Device-Token"),
):
    device = _authenticate(
        x_device_token=x_device_token,
        device_id=deviceId,
        controller_code=controllerCode,
        branch=branch,
    )
    if device is None:
        return _auth_error()
    return success(_service.check(device))


@router.get("/artifacts/{artifact_token}")
async def device_ota_artifact(
    artifact_token: str,
    deviceId: str | None = Query(default=None),
    controllerCode: str | None = Query(default=None),
    branch: str | None = Query(default=None),
    x_device_token: str | None = Header(default=None, alias="X-Device-Token"),
):
    device = _authenticate(
        x_device_token=x_device_token,
        device_id=deviceId,
        controller_code=controllerCode,
        branch=branch,
    )
    if device is None:
        return _auth_error()
    try:
        path, target = _service.open_artifact(artifact_token=artifact_token, device=device)
    except ContentCodedError as exc:
        return _coded(exc)
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=f"{target.get('firmware_version') or 'firmware'}.bin",
    )


@router.post("/report")
async def device_ota_report(
    request: Request,
    x_device_token: str | None = Header(default=None, alias="X-Device-Token"),
):
    body = await request.json()
    if not isinstance(body, dict):
        return _coded(ContentCodedError("validation_error"))
    device = _authenticate(
        x_device_token=x_device_token,
        device_id=body.get("deviceId") or body.get("device_id"),
        controller_code=body.get("controllerCode") or body.get("controller_code"),
        branch=body.get("branch"),
    )
    if device is None:
        return _auth_error()
    try:
        data = _service.report(
            device,
            target_id=body.get("targetId") or body.get("target_id"),
            status=str(body.get("status") or ""),
            error_code=body.get("errorCode") or body.get("error_code"),
            installed_version=body.get("installedFirmwareVersion")
            or body.get("installed_firmware_version"),
            bytes_received=_optional_int(body.get("bytesReceived") or body.get("bytes_received")),
            bytes_total=_optional_int(body.get("bytesTotal") or body.get("bytes_total")),
            progress_percent=_optional_int(
                body.get("progressPercent") or body.get("progress_percent")
            ),
        )
    except ContentCodedError as exc:
        return _coded(exc)
    return success(data)
