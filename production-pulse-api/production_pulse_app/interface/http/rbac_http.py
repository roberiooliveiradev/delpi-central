from __future__ import annotations

from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse

from production_pulse_app.application.security import production_pulse_permissions as perms
from production_pulse_app.core.responses import error


def user_from_request(request: Request):
    return getattr(request.state, "user", None)


def permission_denied(message: str = "Sem permissão para esta operação.") -> JSONResponse:
    payload = error(message, code="forbidden", status_code=403)
    status_code = payload.pop("_status_code", 403)
    return JSONResponse(status_code=status_code, content=payload)


def guard_permission(request: Request, checker: Callable[[object | None], None]) -> JSONResponse | None:
    user = user_from_request(request)
    try:
        checker(user)
    except PermissionError as exc:
        return permission_denied(str(exc))
    return None


def guard_view_devices(request: Request) -> JSONResponse | None:
    return guard_permission(request, perms.assert_can_view_devices)


def guard_manage_devices(request: Request) -> JSONResponse | None:
    return guard_permission(request, perms.assert_can_manage_devices)


def guard_admin_command(request: Request) -> JSONResponse | None:
    return guard_permission(request, perms.assert_can_admin_command)


def guard_operator(request: Request) -> JSONResponse | None:
    return guard_permission(request, perms.assert_can_operator)


def guard_branch_access(request: Request, branch: str) -> JSONResponse | None:
    user = user_from_request(request)
    try:
        perms.assert_branch_access(user, branch)
    except PermissionError as exc:
        return permission_denied(str(exc))
    return None


def guard_device_branch_access(request: Request, device_row: dict) -> JSONResponse | None:
    user = user_from_request(request)
    try:
        perms.assert_device_branch_access(user, device_row)
    except PermissionError as exc:
        return permission_denied(str(exc))
    return None


def resolve_list_branches(request: Request, branch: str | None) -> tuple[list[str] | None, JSONResponse | None]:
    user = user_from_request(request)
    allowed = perms.branch_codes_for_access(user)
    if not allowed and not perms.is_admin(user):
        return None, permission_denied("Sem permissão para nenhuma filial.")

    if branch:
        try:
            perms.assert_branch_access(user, branch)
        except PermissionError as exc:
            return None, permission_denied(str(exc))
        return [branch], None

    if perms.is_admin(user):
        return None, None
    return allowed, None
