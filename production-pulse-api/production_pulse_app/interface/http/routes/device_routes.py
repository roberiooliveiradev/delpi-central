from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, Request

from production_pulse_app.application.services.device_binding_service import (
    BindingNotFoundError,
    BindingValidationError,
    DeviceBindingService,
)
from production_pulse_app.application.services.device_service import (
    DeviceConflictError,
    DeviceNotFoundError,
    DeviceService,
    DeviceValidationError,
)
from production_pulse_app.core.responses import error, success
from production_pulse_app.domain.services.device_serialization_service import parse_device_id
from production_pulse_app.interface.http.schemas.binding_schemas import DeviceBindingBody
from production_pulse_app.interface.http.schemas.device_schemas import (
    DeviceCreateBody,
    DevicePatchBody,
    DeviceReplaceBody,
    body_to_dict,
)

router = APIRouter(prefix="/devices", tags=["Devices"])
_service = DeviceService()
_binding_service = DeviceBindingService()


def _actor_sub(request: Request) -> str | None:
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return getattr(user, "sub", None) or getattr(user, "id", None)


def _handle_domain_errors(exc: Exception):
    if isinstance(exc, (DeviceValidationError, BindingValidationError)):
        return error(str(exc), code="validation_error", status_code=422)
    if isinstance(exc, (DeviceNotFoundError, BindingNotFoundError)):
        message = (
            "Amarração não encontrada."
            if isinstance(exc, BindingNotFoundError)
            else "Dispositivo não encontrado."
        )
        return error(message, code="not_found", status_code=404)
    if isinstance(exc, DeviceConflictError):
        return error(str(exc), code="conflict", status_code=409)
    raise exc


def _json_error(exc: Exception):
    payload = _handle_domain_errors(exc)
    status_code = payload.pop("_status_code", 400)
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status_code, content=payload)


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
        return _json_error(exc)


@router.get("/{device_id}")
async def get_device(device_id: UUID):
    try:
        return success(_service.get_device(device_id))
    except Exception as exc:
        return _json_error(exc)


@router.post("", status_code=201)
async def create_device(request: Request, body: DeviceCreateBody):
    try:
        data = _service.create_device(body_to_dict(body), actor_sub=_actor_sub(request))
        return success(data)
    except Exception as exc:
        return _json_error(exc)


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
        return _json_error(exc)


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
        return _json_error(exc)


@router.delete("/{device_id}")
async def delete_device(request: Request, device_id: UUID):
    try:
        data = _service.delete_device(parse_device_id(str(device_id)), actor_sub=_actor_sub(request))
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.get("/{device_id}/binding")
async def get_device_binding(device_id: UUID):
    try:
        binding = _binding_service.get_active_binding(parse_device_id(str(device_id)))
        return success(binding)
    except Exception as exc:
        return _json_error(exc)


@router.put("/{device_id}/binding")
async def upsert_device_binding(request: Request, device_id: UUID, body: DeviceBindingBody):
    try:
        data = _binding_service.upsert_binding(
            parse_device_id(str(device_id)),
            body.model_dump(by_alias=False, exclude_none=True),
            actor_sub=_actor_sub(request),
        )
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.delete("/{device_id}/binding")
async def delete_device_binding(request: Request, device_id: UUID):
    try:
        _binding_service.delete_active_binding(
            parse_device_id(str(device_id)),
            actor_sub=_actor_sub(request),
        )
        return success(None)
    except Exception as exc:
        return _json_error(exc)


@router.get("/{device_id}/bindings/history")
async def list_binding_history(
    device_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
):
    try:
        data = _binding_service.list_binding_history(
            parse_device_id(str(device_id)),
            page=page,
            page_size=page_size,
        )
        return success(data)
    except Exception as exc:
        return _json_error(exc)
