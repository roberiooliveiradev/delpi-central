from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, Request

from production_pulse_app.application.services.work_center_catalog_service import (
    WorkCenterCatalogUnavailableError,
)
from production_pulse_app.application.services.device_binding_service import (
    BindingNotFoundError,
    DeviceBindingService,
)
from production_pulse_app.application.services.device_command_service import DeviceCommandService
from production_pulse_app.application.services.device_poll_service import (
    DevicePollFailedError,
    DevicePollService,
)
from production_pulse_app.application.services.device_probe_service import (
    DeviceProbeService,
    TestProbeRateLimitError,
)
from production_pulse_app.application.services.device_service import (
    DeviceConflictError,
    DeviceNotFoundError,
    DeviceService,
)
from production_pulse_app.core.responses import error, success
from production_pulse_app.domain.errors import (
    BindingValidationError,
    CommandNotSupportedError,
    DeviceValidationError,
)
from production_pulse_app.infrastructure.content.device_api_messages_content_service import (
    http_error_message,
)
from production_pulse_app.domain.services.device_serialization_service import parse_device_id
from production_pulse_app.interface.http.content_coded_error_response import content_coded_error_response
from production_pulse_app.interface.http.device_connectivity_responses import device_poll_failed_response
from production_pulse_app.interface.http.rbac_http import (
    guard_admin_command,
    guard_branch_access,
    guard_device_branch_access,
    guard_manage_devices,
    guard_view_devices,
    resolve_list_branches,
)
from production_pulse_app.interface.http.schemas.binding_schemas import DeviceBindingBody
from production_pulse_app.interface.http.schemas.device_schemas import (
    DeviceCreateBody,
    DevicePatchBody,
    DeviceReplaceBody,
    DeviceTestProbeBody,
    body_to_dict,
)

router = APIRouter(prefix="/devices", tags=["Devices"])
_service = DeviceService()
_binding_service = DeviceBindingService()
_poll_service = DevicePollService()
_probe_service = DeviceProbeService()
_command_service = DeviceCommandService()


def _actor_sub(request: Request) -> str | None:
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    return getattr(user, "sub", None) or getattr(user, "id", None)


def _authorization_header(request: Request) -> str | None:
    raw = request.headers.get("Authorization")
    if raw and raw.strip():
        return raw.strip()
    return None


async def _optional_json_body(request: Request) -> dict[str, Any] | None:
    try:
        body = await request.json()
    except Exception:
        return None
    return body if isinstance(body, dict) else None


def _handle_domain_errors(exc: Exception):
    if isinstance(exc, PermissionError):
        return error(str(exc), code="forbidden", status_code=403)
    if isinstance(exc, (DeviceValidationError, BindingValidationError, CommandNotSupportedError)):
        raise exc
    if isinstance(exc, WorkCenterCatalogUnavailableError):
        return error(str(exc), code="upstream_unavailable", status_code=503)
    if isinstance(exc, (DeviceNotFoundError, BindingNotFoundError)):
        message = (
            http_error_message("notFoundBinding")
            if isinstance(exc, BindingNotFoundError)
            else http_error_message("notFoundDevice")
        )
        return error(message, code="not_found", status_code=404)
    if isinstance(exc, DeviceConflictError):
        return error(http_error_message("duplicateIp", fallback=str(exc)), code="conflict", status_code=409)
    if isinstance(exc, TestProbeRateLimitError):
        return error(str(exc), code="rate_limit_exceeded", status_code=429)
    raise exc


def _json_error(exc: Exception):
    if isinstance(exc, (DeviceValidationError, BindingValidationError, CommandNotSupportedError)):
        return content_coded_error_response(exc)
    payload = _handle_domain_errors(exc)
    status_code = payload.pop("_status_code", 400)
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status_code, content=payload)


def _load_device_for_request(
    request: Request,
    device_id: UUID,
    *,
    action: str,
) -> tuple[dict[str, Any] | None, Any | None]:
    if action == "view":
        denied = guard_view_devices(request)
    elif action == "manage":
        denied = guard_manage_devices(request)
    elif action == "command":
        denied = guard_admin_command(request)
    else:
        raise ValueError(f"Unsupported RBAC action: {action}")

    if denied is not None:
        return None, denied

    try:
        device = _service.get_device_record(parse_device_id(str(device_id)))
    except Exception as exc:
        return None, _json_error(exc)

    denied = guard_device_branch_access(request, device)
    if denied is not None:
        return None, denied
    return device, None


@router.get("")
async def list_devices(
    request: Request,
    branch: str | None = Query(default=None),
    role: str | None = Query(default=None),
    enabled: bool | None = Query(default=None),
    search: str | None = Query(default=None),
):
    denied = guard_view_devices(request)
    if denied is not None:
        return denied
    branches, denied = resolve_list_branches(request, branch)
    if denied is not None:
        return denied
    try:
        data = _service.list_devices(
            branch=branch,
            branches=branches,
            role=role,
            enabled=enabled,
            search=search,
        )
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.post("/test-probe")
async def test_probe(request: Request, body: DeviceTestProbeBody):
    denied = guard_manage_devices(request) or guard_branch_access(request, body.branch)
    if denied is not None:
        return denied
    try:
        data = _probe_service.probe_device(
            branch=body.branch,
            ip_address=body.ip_address,
            driver_key=body.driver_key,
            actor_sub=_actor_sub(request),
        )
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.post("/poll-all")
async def poll_all_devices(
    request: Request,
    branch: str | None = Query(default=None),
    role: str | None = Query(default=None),
):
    denied = guard_manage_devices(request)
    if denied is not None:
        return denied
    branches, denied = resolve_list_branches(request, branch)
    if denied is not None:
        return denied
    try:
        data = _poll_service.poll_all(branch=branch, branches=branches, role=role)
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.get("/{device_id}/commands")
async def list_device_commands(
    request: Request,
    device_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
):
    _, denied = _load_device_for_request(request, device_id, action="view")
    if denied is not None:
        return denied
    try:
        data = _command_service.list_commands(
            parse_device_id(str(device_id)),
            page=page,
            page_size=page_size,
            authorization=_authorization_header(request),
        )
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.post("/{device_id}/commands/{command_key}")
async def execute_device_command(request: Request, device_id: UUID, command_key: str):
    _, denied = _load_device_for_request(request, device_id, action="command")
    if denied is not None:
        return denied
    try:
        payload = await _optional_json_body(request)
        data = _command_service.execute_command(
            parse_device_id(str(device_id)),
            command_key,
            actor_sub=_actor_sub(request),
            payload=payload,
        )
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.get("/{device_id}/live")
async def get_device_live(request: Request, device_id: UUID):
    _, denied = _load_device_for_request(request, device_id, action="view")
    if denied is not None:
        return denied
    try:
        return success(_poll_service.read_live(parse_device_id(str(device_id))))
    except DevicePollFailedError as exc:
        return device_poll_failed_response(exc)
    except Exception as exc:
        return _json_error(exc)


@router.post("/{device_id}/poll")
async def poll_device(request: Request, device_id: UUID):
    _, denied = _load_device_for_request(request, device_id, action="view")
    if denied is not None:
        return denied
    try:
        return success(_poll_service.poll_and_persist(parse_device_id(str(device_id)), source="manual"))
    except DevicePollFailedError as exc:
        return device_poll_failed_response(exc)
    except Exception as exc:
        return _json_error(exc)


@router.get("/{device_id}/readings")
async def list_device_readings(
    request: Request,
    device_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    recorded_from: str | None = Query(default=None, alias="from"),
    recorded_to: str | None = Query(default=None, alias="to"),
    metric: str | None = Query(default=None),
):
    _, denied = _load_device_for_request(request, device_id, action="view")
    if denied is not None:
        return denied
    try:
        from datetime import datetime

        def _parse_dt(value: str | None) -> datetime | None:
            if not value:
                return None
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)

        data = _poll_service.list_readings(
            parse_device_id(str(device_id)),
            page=page,
            page_size=page_size,
            recorded_from=_parse_dt(recorded_from),
            recorded_to=_parse_dt(recorded_to),
            metric_key=metric,
        )
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.post("/{device_id}/test")
async def test_existing_device(request: Request, device_id: UUID):
    _, denied = _load_device_for_request(request, device_id, action="manage")
    if denied is not None:
        return denied
    try:
        device = _service.get_device_record(parse_device_id(str(device_id)))
        data = _probe_service.probe_existing_device(device, actor_sub=_actor_sub(request))
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.get("/{device_id}")
async def get_device(request: Request, device_id: UUID):
    _, denied = _load_device_for_request(request, device_id, action="view")
    if denied is not None:
        return denied
    try:
        return success(_service.get_device(device_id))
    except Exception as exc:
        return _json_error(exc)


@router.post("", status_code=201)
async def create_device(request: Request, body: DeviceCreateBody):
    denied = guard_manage_devices(request) or guard_branch_access(request, body.branch)
    if denied is not None:
        return denied
    try:
        data = _service.create_device(body_to_dict(body), actor_sub=_actor_sub(request))
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.put("/{device_id}")
async def replace_device(request: Request, device_id: UUID, body: DeviceReplaceBody):
    _, denied = _load_device_for_request(request, device_id, action="manage")
    if denied is not None:
        return denied
    denied = guard_branch_access(request, body.branch)
    if denied is not None:
        return denied
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
    _, denied = _load_device_for_request(request, device_id, action="manage")
    if denied is not None:
        return denied
    patch_data = body.model_dump(by_alias=False, exclude_none=True)
    if "branch" in patch_data:
        denied = guard_branch_access(request, patch_data["branch"])
        if denied is not None:
            return denied
    try:
        data = _service.patch_device(
            parse_device_id(str(device_id)),
            patch_data,
            actor_sub=_actor_sub(request),
        )
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.delete("/{device_id}")
async def delete_device(request: Request, device_id: UUID):
    _, denied = _load_device_for_request(request, device_id, action="manage")
    if denied is not None:
        return denied
    try:
        data = _service.delete_device(parse_device_id(str(device_id)), actor_sub=_actor_sub(request))
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.get("/{device_id}/binding")
async def get_device_binding(request: Request, device_id: UUID):
    _, denied = _load_device_for_request(request, device_id, action="view")
    if denied is not None:
        return denied
    try:
        binding = _binding_service.get_active_binding(parse_device_id(str(device_id)))
        return success(binding)
    except Exception as exc:
        return _json_error(exc)


@router.put("/{device_id}/binding")
async def upsert_device_binding(request: Request, device_id: UUID, body: DeviceBindingBody):
    _, denied = _load_device_for_request(request, device_id, action="manage")
    if denied is not None:
        return denied
    try:
        data = _binding_service.upsert_binding(
            parse_device_id(str(device_id)),
            body.model_dump(by_alias=False, exclude_none=True),
            actor_sub=_actor_sub(request),
            authorization=_authorization_header(request),
        )
        return success(data)
    except Exception as exc:
        return _json_error(exc)


@router.delete("/{device_id}/binding")
async def delete_device_binding(request: Request, device_id: UUID):
    _, denied = _load_device_for_request(request, device_id, action="manage")
    if denied is not None:
        return denied
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
    request: Request,
    device_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
):
    _, denied = _load_device_for_request(request, device_id, action="view")
    if denied is not None:
        return denied
    try:
        data = _binding_service.list_binding_history(
            parse_device_id(str(device_id)),
            page=page,
            page_size=page_size,
        )
        return success(data)
    except Exception as exc:
        return _json_error(exc)
