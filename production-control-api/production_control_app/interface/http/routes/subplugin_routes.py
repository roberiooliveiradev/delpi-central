from __future__ import annotations

from fastapi import APIRouter, Request

from production_control_app.composition.pc_composer import build_catalog_service
from production_control_app.core.responses import fail, ok
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Subplugins"])


@router.get("/subplugins")
def list_subplugins(request: Request):
    user = resolve_user(request)
    try:
        items = build_catalog_service().list_visible(user)
    except PermissionError as exc:
        return fail(str(exc), 403)
    return ok({"items": [item.to_dict() for item in items]})
