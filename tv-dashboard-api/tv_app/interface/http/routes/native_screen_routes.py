from __future__ import annotations

from fastapi import APIRouter, Request

from tv_app.application.services.native_screen_data_service import NativeScreenDataService
from tv_app.core.responses import fail, ok
from tv_app.core.security import TV_READ, assert_permission
from tv_app.interface.http.auth_http import resolve_user

router = APIRouter(prefix="/native-screens", tags=["Native Screens"])
_service = NativeScreenDataService()


@router.get("")
def list_native_screens(request: Request):
    user = resolve_user(request)
    try:
        assert_permission(user, TV_READ)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok({"items": _service.catalog()})
