from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, Request

from production_pulse_app.application.services.device_service import (
    DeviceConflictError,
    DeviceNotFoundError,
    DeviceService,
    DeviceValidationError,
)
from production_pulse_app.core.responses import error, success
from production_pulse_app.domain.services.device_serialization_service import parse_device_id
from production_pulse_app.interface.http.schemas.device_schemas import (
    DeviceCreateBody,
    DevicePatchBody,
    DeviceReplaceBody,
    body_to_dict,
)

router = APIRouter(prefix="/devices", tags=["Devices"])
_service = DeviceService()


def _actor_sub(request: Request) -> str | None:
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return getattr(user, "sub", None) or getattr(user, "id", None)


def _handle_domain_errors(exc: Exception):
    if isinstance(exc, DeviceValidationError):
        return error(str(exc), code="validation_error", status_code=422)
    if isinstance(exc, DeviceNotFoundError):
        return error("Dispositivo não encontrado.", code="not_found", status_code=404)
    if isinstance(exc, DeviceConflictError):
        return error(str(exc), code="conflict", status_code=409)
    raise exc


@router.get("")
async def list_devices(
    branch: str | None = Query(default=None),
    role: str | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    search: str | None = Query(default=None),
):
    try:
        data = _service.list_devices(branch=branch, role=role, enabled=enabled, search=search)
        return success(data)
    except Exception as exc:
        payload = _handle_domain_errors(exc)
        status_code = payload.pop("_status_code", 400)
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=status_code, content=payload)


@router.get("/{device_id}")
async def get_device(device_id: UUID):
    try:
        return success(_service.get_device(device_id))
    except Exception as exc:
        payload = _handle_domain_errors(exc)
        status_code = payload.pop("_status_code", 400)
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=status_code, content=payload)


@router.post("", status_code=201)
async def create_device(request: Request, body: DeviceCreateBody):
    try:
        data = _service.create_device(body_to_dict(body), actor_sub=_actor_sub(request))
        return success(data)
    except Exception as exc:
        payload = _handle_domain_errors(exc)
        status_code = payload.pop("_status_code", 400)
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=status_code, content=payload)


@router.put("/{device_id}")
async def replace_device(request: Request, device_id: UUID, body: DeviceReplaceBody):
    try:
        data = _service.replace_device(
            parse_device_id(str(device_id)),
            body_to_dict(body),
            actor_sub=_actor_sub(request),
        )
        return success(data)
    except Exception as exc:
        payload = _handle_domain_errors(exc)
        status_code = payload.pop("_status_code", 400)
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=status_code, content=payload)


@router.patch("/{device_id}")
async def patch_device(request: Request, device_id: UUID, body: DevicePatchBody):
    try:
        data = _service.patch_device(
            parse_device_id(str(device_id)),
            body.model_dump(by_alias=False, exclude_none=True),
            actor_sub=_actor_sub(request),
        )
        return success(data)
    except Exception as exc:
        payload = _handle_domain_errors(exc)
        status_code = payload.pop("_status_code", 400)
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=status_code, content=payload)


@router.delete("/{device_id}")
async def delete_device(request: Request, device_id: UUID):
    try:
        data = _service.delete_device(parse_device_id(str(device_id)), actor_sub=_actor_sub(request))
        return success(data)
    except Exception as exc:
        payload = _handle_domain_errors(exc)
        status_code = payload.pop("_status_code", 400)
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=status_code, content=payload)
